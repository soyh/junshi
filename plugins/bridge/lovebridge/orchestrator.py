"""Reply orchestrator: dedup -> debounce -> record -> draft -> send -> record."""

from __future__ import annotations

import asyncio
import json
import os
import random
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from .app_client import AppError, platform_of
from .channels.base import Channel, InboundEvent
from .console import write_line
from .config import BotConfig, Config
from .state import StateStore


@dataclass
class TurnResult:
    contact_id: str
    conversation_id: str
    inbound: int
    reply: str | None = None
    sent: bool = False
    reason: str = ""


class Orchestrator:
    def __init__(
        self,
        config: Config,
        app,
        channel: Channel,
        state: StateStore,
        *,
        log: Callable[[str], None] = write_line,
        now: Callable[[], datetime] = datetime.now,
        rng: Callable[[], float] = random.random,
    ) -> None:
        self.config = config
        self.app = app
        self.channel = channel
        self.state = state
        self._log = log
        setter = getattr(channel, "set_logger", None)
        if callable(setter):
            setter(log)
        self._now = now
        self._rng = rng

        self._pending: dict[str, list[InboundEvent]] = {}
        self._timers: dict[str, asyncio.Task] = {}
        self._first_at: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._semaphore = asyncio.Semaphore(max(1, config.bot.max_concurrency))
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_event = asyncio.Event()
        self.results: list[TurnResult] = []
        self._background: list[asyncio.Task] = []
        self._heartbeat_enabled = True
        self._last_state = ""
        self._platform_cache: dict[str, tuple[str, str | None]] = {}

    # -- lifecycle --------------------------------------------------------
    START_TIMEOUT = 180.0
    HEARTBEAT_SECONDS = 20.0
    RETRY_SECONDS = 10.0
    MAX_ATTEMPTS = 3
    BACKOFF = (8, 20, 45)
    DEFER_SECONDS = 120
    #: 排队消息最长等 3 分钟。超过就当场记为“失败”，让用户在面板里看得见、
    #: 自己决定手动回还是计入已回，而不是静静躺上一小时。
    LONG_WAIT_LIMIT = 180

    async def run(self) -> None:
        self._loop = asyncio.get_running_loop()
        self.channel.set_handler(self._on_event)
        self._background = []
        # Report before the channel is ready: a slow login window must not look
        # like a dead process on the status panel.
        self._start_state = "启动中"
        self._background.append(asyncio.create_task(self._heartbeat_loop()))
        try:
            await asyncio.wait_for(self.channel.start(), timeout=self.START_TIMEOUT)
            self._start_state = ""
        except Exception as exc:
            self._start_state = "启动失败"
            self._log(f"[bridge] channel start failed: {exc!r}; will retry every 30s")
            self._background.append(asyncio.create_task(self._retry_start()))
        self._background.append(asyncio.create_task(self._health_loop()))
        self._background.append(asyncio.create_task(self._outbox_loop()))
        await self._report_once()
        initial = await self._channel_status()
        if initial != "online":
            self._log(
                f"[bridge] channel not ready ({initial}); complete the platform login "
                "in the browser window the bridge opened"
            )
        self._log(
            f"[bridge] started channel={self.config.channel.kind} "
            f"dry_run={self.config.bot.dry_run} app={self.config.app.base_url}"
        )
        await self._stop_event.wait()

    async def stop(self) -> None:
        self._stop_event.set()
        self._write_status("已停止")
        for task in self._timers.values():
            task.cancel()
        for task in self._background:
            task.cancel()
        await self.channel.stop()

    # -- background -------------------------------------------------------
    async def _retry_start(self) -> None:
        while True:
            await asyncio.sleep(30)
            try:
                await asyncio.wait_for(self.channel.start(), timeout=self.START_TIMEOUT)
            except Exception as exc:
                self._log(f"[bridge] channel start retry failed: {exc!r}")
                continue
            self._start_state = ""
            self._log("[bridge] channel started after retry")
            await self._report_once()
            return

    def _status_path(self):  # noqa: ANN201
        return self.config.source_path.parent / "status.json"

    def _write_status(self, state: str, error: str = "") -> None:
        """Local, per-profile snapshot — the desktop panel reads this file.

        The server heartbeat is keyed by (user, channel) and cannot tell two
        profiles of the same platform apart, so the local file is authoritative.
        """
        outbox = self.state.outbox_counts()
        payload = {
            "status": state,
            "pid": os.getpid(),
            "channel": self.config.channel.kind,
            "dry_run": self.config.bot.dry_run,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "replies_today": self.state.total_today(self._today()),
            "outbox": outbox,
        }
        if error:
            payload["error"] = error
        elif outbox["queued"] or outbox["failed"]:
            payload["error"] = self.state.last_failure()[:200]
        try:
            self._status_path().write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass

    async def _report_once(self) -> None:
        try:
            state = await self._channel_status()
            self._last_state = state
            self._write_status(state)
            if self._heartbeat_enabled:
                await self.app.heartbeat(
                    self.config.channel.kind,
                    state,
                    self.state.total_today(self._today()),
                    detail=str(getattr(self.channel, "_identity", ""))[:200],
                )
        except AppError as exc:
            if exc.status == 404:
                self._heartbeat_enabled = False
                self._log("[bridge] heartbeat endpoint not deployed; disabled")
            else:
                self._log(f"[bridge] heartbeat failed: {exc}")
        except Exception as exc:  # never let monitoring kill the bridge
            self._log(f"[bridge] heartbeat error: {exc!r}")

    def _sync_status(self) -> None:
        """Rewrite status.json after an outbox change (panel shows it instantly)."""
        try:
            self._write_status(self._last_state or "online")
        except Exception:  # status is best effort only
            pass

    async def _channel_status(self) -> str:
        """Report what the platform actually shows, not just that the process lives."""
        if getattr(self, "_start_state", ""):
            return self._start_state
        provider = getattr(self.channel, "status", None)
        if provider is not None:
            try:
                return str(await provider())
            except Exception:
                return "异常"
        healthy = getattr(self.channel, "healthy", None)
        if healthy is None:
            return "online"
        try:
            return "online" if await healthy() else "未登录"
        except Exception:
            return "异常"

    async def _heartbeat_loop(self) -> None:
        while True:
            await self._report_once()
            await asyncio.sleep(self.HEARTBEAT_SECONDS)

    async def _health_loop(self) -> None:
        provider = getattr(self.channel, "status", None) or getattr(self.channel, "healthy", None)
        if provider is None:
            return
        while True:
            await asyncio.sleep(60)
            try:
                value = await provider()
                ok = value in (True, "online")
            except Exception as exc:
                ok = False
                self._log(f"[bridge] health check error: {exc!r}")
            if not ok:
                self._log("[bridge] channel unhealthy: session may have expired")

    # -- intake -----------------------------------------------------------
    def _on_event(self, event: InboundEvent) -> None:
        loop = self._loop
        if loop is None:
            return
        loop.call_soon_threadsafe(self._accept, event)

    def _accept(self, event: InboundEvent) -> None:
        if not self.state.first_seen(event.message_id, event.contact_id):
            return
        # Persist before any network work: a crash or a failed turn must not
        # silently drop the message, it owes a reply until we mark it.
        self.state.enqueue(
            event.message_id,
            event.contact_id,
            event.text,
            contact_name=event.contact_name,
            sent_at=event.timestamp,
            is_group=event.is_group,
        )

        bot = self.config.bot
        contact_id = event.contact_id
        self._pending.setdefault(contact_id, []).append(event)
        now = time.monotonic()
        self._first_at.setdefault(contact_id, now)

        previous = self._timers.pop(contact_id, None)
        if previous is not None:
            previous.cancel()

        overdue = (now - self._first_at[contact_id]) >= bot.max_debounce_seconds
        if overdue:
            task = asyncio.create_task(self._process(contact_id))
        else:
            task = asyncio.create_task(self._debounced(contact_id))
        self._timers[contact_id] = task

    async def _debounced(self, contact_id: str) -> None:
        try:
            await asyncio.sleep(self.config.bot.debounce_seconds)
        except asyncio.CancelledError:
            return
        await self._process(contact_id)

    async def _process(self, contact_id: str) -> None:
        events = self._pending.pop(contact_id, [])
        self._timers.pop(contact_id, None)
        self._first_at.pop(contact_id, None)
        if not events:
            return
        lock = self._locks.setdefault(contact_id, asyncio.Lock())
        async with self._semaphore:
            async with lock:
                try:
                    result = await self._turn(contact_id, events)
                    self.results.append(result)
                except Exception as exc:  # keep the bridge alive no matter what
                    message = f"{type(exc).__name__}: {exc}"
                    self._log(f"[bridge] turn failed contact={contact_id}: {exc!r}")
                    self._finish_outbox(contact_id, events, error=message)
                    return
                self._finish_outbox(contact_id, events, result)

    # -- outbox -----------------------------------------------------------
    def _finish_outbox(
        self,
        contact_id: str,
        events: list[InboundEvent],
        result: TurnResult | None = None,
        *,
        error: str = "",
    ) -> None:
        """Mark the owed replies: sent, skipped, deferred or queued for retry."""
        try:
            self._apply_outbox(contact_id, events, result, error=error)
        finally:
            # The panel polls status.json; refresh it the moment a reply is
            # queued or sent instead of waiting for the next heartbeat.
            self._sync_status()

    def _apply_outbox(
        self,
        contact_id: str,
        events: list,
        result,
        *,
        error: str = "",
    ) -> None:
        wanted = {event.message_id for event in events}
        rows = [
            row for row in self.state.outbox_pending(contact_id)
            if row["message_id"] in wanted
        ]
        if not rows:
            return
        ids = [int(row["id"]) for row in rows]
        attempts = max(int(row["attempts"]) for row in rows)

        if error:
            attempts += 1
            if attempts >= self.MAX_ATTEMPTS:
                self.state.outbox_finish(ids, "failed", error, attempts=attempts)
                self._log(
                    f"[bridge] gave up contact={contact_id} after {attempts} attempts: {error}"
                )
            else:
                delay = self.BACKOFF[min(attempts - 1, len(self.BACKOFF) - 1)]
                self.state.outbox_finish(
                    ids, "queued", error, self._later(delay), attempts=attempts
                )
                self._log(
                    f"[bridge] retry contact={contact_id} in {delay}s "
                    f"(attempt {attempts}/{self.MAX_ATTEMPTS}): {error}"
                )
            return

        reason = (result.reason if result else "").strip()
        if result is not None and result.sent:
            self.state.outbox_finish(ids, "sent")
            return
        if reason in ("quiet hours", "daily cap", "paused"):
            # Not a failure: keep the message and try again later.
            delay = self.DEFER_SECONDS
            if reason == "daily cap":
                delay = self._seconds_until_tomorrow()
            waited = self._waited_seconds(rows)
            if delay > self.LONG_WAIT_LIMIT or waited >= self.LONG_WAIT_LIMIT:
                # 等太久（每日上限要等到明天、安静时段一直没结束）就别挂着：
                # 直接显示成失败，用户看到后手动回一句，再点“计入已回”。
                if delay > self.LONG_WAIT_LIMIT:
                    note = f"{reason}（下次要等 {int(delay) // 60} 分钟）"
                else:
                    note = f"{reason}（已等 {int(waited) // 60} 分钟）"
                note += "，超过 3 分钟未发出"
                self.state.outbox_finish(
                    ids, "failed", note, attempts=max(attempts, self.MAX_ATTEMPTS)
                )
                self._log(f"[bridge] give up contact={contact_id}: {note}")
                return
            self.state.outbox_finish(ids, "queued", reason, self._later(delay))
            self._log(f"[bridge] defer contact={contact_id} ({reason}) for {delay}s")
            return
        self.state.outbox_finish(ids, "skipped", reason or "no reply")
        self._log(f"[bridge] skip contact={contact_id}: {reason or 'no reply'}")

    async def _outbox_loop(self) -> None:
        while True:
            await asyncio.sleep(self.RETRY_SECONDS)
            try:
                await self.drain_outbox()
            except Exception as exc:  # the loop must outlive any one failure
                self._log(f"[bridge] outbox pass failed: {exc!r}")

    async def _send_photo(
        self,
        contact_id: str,
        conversation_id: str,
        person_id: str,
        photo_id: str,
        caption: str,
        events: list[InboundEvent],
    ) -> TurnResult:
        """Deliver one of the user's own photos, with an optional line of text."""
        sender = getattr(self.channel, "send_image", None)
        if sender is None:
            self._log(
                f"[bridge] 这个通道还不能发图（{type(self.channel).__name__}），改为只发文字"
            )
            if not caption.strip():
                return TurnResult(
                    contact_id, conversation_id, len(events), reason="photo unsupported"
                )
            await self._human_delay()
            if not self.state.claim_reply(contact_id, caption):
                return TurnResult(
                    contact_id, conversation_id, len(events), reason="duplicate suppressed"
                )
            await self.channel.send(contact_id, caption, is_group=bool(events[0].is_group))
            try:
                await self.app.add_message(conversation_id, "user", caption)
            except Exception as exc:
                self._log(f"[bridge] caption delivered but not recorded: {exc!r}")
            return TurnResult(
                contact_id, conversation_id, len(events), reply=caption,
                reason="photo unsupported, text only",
            )
        marker = f"photo:{photo_id}"
        if not self.state.claim_reply(contact_id, marker):
            return TurnResult(
                contact_id, conversation_id, len(events), reason="duplicate suppressed"
            )
        path = ""
        try:
            content, mime = await self.app.fetch_photo(photo_id)
            suffix = {"image/png": ".png", "image/webp": ".webp"}.get(mime, ".jpg")
            handle = tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix, prefix="junshi-photo-"
            )
            handle.write(content)
            handle.close()
            path = handle.name
            await sender(contact_id, path, caption or "")
        except Exception as exc:
            self.state.release_reply(contact_id, marker)
            self._log(f"[bridge] 发图失败 contact={contact_id}: {exc!r}")
            raise
        finally:
            if path:
                try:
                    os.unlink(path)
                except OSError:
                    pass
        if caption.strip():
            try:
                await self.app.add_message(conversation_id, "user", caption)
            except Exception as exc:
                self._log(f"[bridge] caption delivered but not recorded: {exc!r}")
        try:
            self.state.bump(self._today(), contact_id)
        except Exception:
            pass
        self._log(f"[bridge] 发出照片 contact={contact_id} photo={photo_id}")
        return TurnResult(
            contact_id, conversation_id, len(events), reply=caption or "[照片]",
            reason="photo sent",
        )

    async def drain_outbox(self) -> int:
        """Retry every owed reply that is due. Returns how many were handled."""
        if await self._channel_status() not in ("online",):
            return 0
        now = self._now().isoformat(timespec="seconds")
        grouped: dict[str, list[dict]] = {}
        for row in self.state.outbox_due(now):
            grouped.setdefault(row["contact_id"], []).append(row)
        handled = 0
        for contact_id, items in grouped.items():
            lock = self._locks.setdefault(contact_id, asyncio.Lock())
            async with self._semaphore:
                async with lock:
                    # The live path may have answered while we waited for the lock.
                    pending = {
                        int(row["id"]): row
                        for row in self.state.outbox_pending(contact_id)
                    }
                    chosen = [pending[int(row["id"])] for row in items
                              if int(row["id"]) in pending]
                    if not chosen:
                        continue
                    events = [_event_from_row(row) for row in chosen]
                    try:
                        result = await self._turn(contact_id, events)
                    except Exception as exc:
                        message = f"{type(exc).__name__}: {exc}"
                        self._log(f"[bridge] retry failed contact={contact_id}: {exc!r}")
                        self._finish_outbox(contact_id, events, error=message)
                    else:
                        self.results.append(result)
                        self._finish_outbox(contact_id, events, result)
                    handled += 1
        return handled

    def _waited_seconds(self, rows: list[dict]) -> float:
        """How long the oldest of these queued rows has already been waiting."""
        oldest = min((str(row.get("created_at") or "") for row in rows), default="")
        try:
            created = datetime.fromisoformat(oldest)
        except ValueError:
            return 0.0
        return max(0.0, (self._now() - created).total_seconds())

    def _later(self, seconds: float | int) -> str:
        return (self._now() + timedelta(seconds=int(seconds))).isoformat(timespec="seconds")

    def _seconds_until_tomorrow(self) -> int:
        now = self._now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
        return max(60, int((tomorrow - now).total_seconds()))

    # -- one conversation turn -------------------------------------------
    async def _turn(self, contact_id: str, events: list[InboundEvent]) -> TurnResult:
        bot = self.config.bot
        contact = self.state.get_contact(contact_id)

        if self.state.paused():
            return TurnResult(contact_id, "", 0, reason="paused")

        if events[0].is_group and not bot.reply_to_groups:
            return TurnResult(contact_id, "", 0, reason="group ignored")

        if contact is None:
            if not bot.auto_create_person:
                return TurnResult(contact_id, "", 0, reason="unmapped contact")
            handle = contact_id.split(":", 1)[-1]
            platform = platform_of(contact_id)
            # A human can write from several apps. Ask the server first: if this
            # handle is already on someone's record, reuse that person instead of
            # creating a second person (and a second conversation) for them.
            known = None
            try:
                known = await self.app.resolve_channel(platform, handle)
            except Exception as exc:
                self._log(f"[bridge] channel resolve failed: {exc!r}")
            if known:
                self.state.save_contact(
                    contact_id,
                    known["person_id"],
                    known["conversation_id"],
                    events[0].contact_name,
                )
                contact = self.state.get_contact(contact_id)
                self._log(
                    f"[bridge] recognised {contact_id} as person={known['person_id']}"
                    f"（{known.get('person_name') or ''}），复用同一会话"
                )
            else:
                person = await self.app.find_or_create_person(
                    events[0].contact_name, contact_id, bot.auto_merge_same_name
                )
                primary = await self.app.ensure_primary_conversation(person["id"])
                self.state.save_contact(
                    contact_id, person["id"], primary["id"], events[0].contact_name
                )
                contact = self.state.get_contact(contact_id)
                self._log(
                    f"[bridge] mapped {contact_id} -> person={person['id']} conversation={primary['id']}"
                )
                try:
                    await self.app.link_channel(
                        person["id"], platform, handle, events[0].contact_name
                    )
                except Exception as exc:
                    self._log(f"[bridge] channel link failed: {exc!r}")

        if contact is None or not contact["enabled"]:
            return TurnResult(contact_id, "", 0, reason="contact disabled")

        person_id = contact["person_id"]
        primary = await self.app.ensure_primary_conversation(person_id)
        conversation_id = primary["id"]
        if contact["conversation_id"] != conversation_id:
            self.state.save_contact(
                contact_id, person_id, conversation_id, contact.get("label")
            )
            self._log(
                f"[bridge] repointed {contact_id} to primary conversation {conversation_id}"
            )

        platform, account_id = await self._platform_identity(
            contact_id, person_id, events[0].contact_name
        )
        await self.app.ensure_scoped(conversation_id, person_id)

        mine = [event for event in events if event.is_self]
        if mine:
            # A reply the user typed in the app itself: keep it (it teaches the
            # style profile and keeps the archive honest) and cancel anything
            # queued for this person — otherwise we answer on top of them.
            for event in mine:
                try:
                    await self.app.add_message_once(
                        conversation_id,
                        "user",
                        event.text,
                        operation_id=str(uuid.uuid5(uuid.NAMESPACE_URL, event.message_id)),
                        sent_at=datetime.fromtimestamp(event.timestamp or time.time())
                        .astimezone()
                        .isoformat(timespec="seconds"),
                    )
                except Exception as exc:
                    self._log(f"[bridge] manual reply not recorded: {exc!r}")
            dropped = self.state.clear_pending(contact_id, reason="你手动回了这条")
            self._log(
                f"[bridge] 检测到你手动回复 contact={contact_id}: {mine[-1].text[:40]!r}"
                + (f"，已取消 {dropped} 条排队回复" if dropped else "")
            )
            events = [event for event in events if not event.is_self]
            if not events:
                return TurnResult(contact_id, conversation_id, len(mine), reason="manual reply")

        for event in events:
            text = event.text
            media_url = (event.raw or {}).get("media_url")
            if media_url:
                described = await self._describe_media(conversation_id, str(media_url))
                if described:
                    text = f"{text}（看图：{described}）"
            await self.app.add_message_once(
                conversation_id,
                "person",
                text,
                operation_id=str(uuid.uuid5(uuid.NAMESPACE_URL, event.message_id)),
                sent_at=datetime.fromtimestamp(event.timestamp or time.time())
                .astimezone()
                .isoformat(timespec="seconds"),
                platform=platform,
                platform_account_id=account_id,
            )

        # She may have typed a WeChat id in this burst; the server keeps it on the
        # person record (never overwriting an id the user entered by hand).
        try:
            captured = await self.app.capture_wechat(
                person_id, "\n".join(event.text for event in events)
            )
            if captured:
                self._log(f"[bridge] 记录到对方微信号 {captured}（person={person_id}）")
        except Exception as exc:
            self._log(f"[bridge] wechat capture failed: {exc!r}")

        if self._in_quiet_hours():
            return TurnResult(contact_id, conversation_id, len(events), reason="quiet hours")

        if self.state.total_today(self._today()) >= bot.daily_reply_cap:
            return TurnResult(contact_id, conversation_id, len(events), reason="daily cap")

        # Identity and default rules live on the account (web/PC/phone all read
        # the same record), so only channel-specific rules travel from here.
        context = await self.app.get_reply_context(
            conversation_id,
            self.config.bot.rules,
            wechat_alias=self.config.bot.wechat_alias,
        )
        plan = (context or {}).get("plan") if isinstance(context, dict) else None
        if isinstance(plan, dict) and plan.get("send_allowed") is False:
            # The planner read the situation and decided this turn should not be
            # answered (conflict, cooling off, she asked for space). Holding is a
            # decision, not a failure: nothing is queued for retry.
            tactics = "、".join(
                str(item.get("tactic") or "")
                for item in (plan.get("options") or [])[:3]
                if isinstance(item, dict) and item.get("tactic")
            )
            self._log(
                f"[bridge] hold {contact_id}: {str(plan.get('read') or '')[:60]!r}"
                + (f" tactics={tactics}" if tactics else "")
            )
            return TurnResult(
                contact_id, conversation_id, len(events), reason="plan: hold"
            )
        reply = (context or {}).get("draft")
        reply = reply.strip() if isinstance(reply, str) else ""
        if isinstance(plan, dict) and reply:
            self._log(
                f"[bridge] plan {contact_id}: {plan.get('signal') or '?'}/"
                f"{str(plan.get('tactic') or (plan.get('options') or [{}])[0].get('tactic') or '')[:40]}"
            )

        photo_id = ""
        if isinstance(plan, dict):
            for item in plan.get("options") or []:
                if isinstance(item, dict) and item.get("send") and item.get("photo_id"):
                    photo_id = str(item.get("photo_id"))
                    break
        if not reply and not photo_id:
            return TurnResult(contact_id, conversation_id, len(events), reason="empty draft")
        if len(reply) > bot.max_reply_chars:
            return TurnResult(
                contact_id, conversation_id, len(events), reason=f"draft too long ({len(reply)})"
            )

        if bot.dry_run:
            self._log(f"[dry-run] draft for {contact_id}: {reply[:80]!r}")
            return TurnResult(contact_id, conversation_id, len(events), reply=reply, reason="dry run")

        await self._human_delay()
        if photo_id:
            return await self._send_photo(
                contact_id, conversation_id, person_id, photo_id, reply, events
            )
        if not self.state.claim_reply(contact_id, reply):
            self._log(
                f"[bridge] duplicate reply suppressed contact={contact_id}: {reply[:40]!r}"
            )
            return TurnResult(
                contact_id, conversation_id, len(events), reply=reply,
                reason="duplicate suppressed",
            )
        try:
            await self.channel.send(contact_id, reply, is_group=bool(events[0].is_group))
        except Exception:
            self.state.release_reply(contact_id, reply)
            raise
        try:
            await self.app.add_message(conversation_id, "user", reply)
        except Exception as exc:
            # The sentence is already on the platform; failing to record it must
            # not mark the turn as failed or the retry would send it again.
            self._log(f"[bridge] reply delivered but not recorded: {exc!r}")
        try:
            count = self.state.bump(self._today(), contact_id)
        except Exception as exc:
            count = 0
            self._log(f"[bridge] daily counter update failed: {exc!r}")

        self._log(f"[bridge] replied to {contact_id} ({count} today): {reply[:60]!r}")
        return TurnResult(contact_id, conversation_id, len(events), reply=reply, sent=True)

    # -- helpers ----------------------------------------------------------
    async def _describe_media(self, conversation_id: str, url: str) -> str:
        """Download an inbound picture and let the app's vision model describe it."""
        fetch = getattr(self.channel, "fetch_media", None)
        if fetch is None:
            return ""
        try:
            content = await fetch(url)
        except Exception as exc:
            self._log(f"[bridge] media download failed: {exc!r}")
            return ""
        if not content:
            return ""
        try:
            text = await self.app.describe_media(conversation_id, content)
        except Exception as exc:  # never let vision break the answered turn
            self._log(f"[bridge] media describe failed: {exc!r}")
            return ""
        if text:
            self._log(f"[bridge] described inbound image: {text[:60]!r}")
        return text

    async def _platform_identity(
        self, contact_id: str, person_id: str, contact_name: str
    ) -> tuple[str, str | None]:
        """Platform tag and person-platform-account id for message provenance."""
        platform = platform_of(contact_id)
        cached = self._platform_cache.get(contact_id)
        if cached and cached[0] == person_id:
            return platform, cached[1]
        account_id: str | None = None
        try:
            account_id = await self.app.ensure_platform_source(
                person_id,
                "",
                platform,
                contact_id.split(":", 1)[-1],
                contact_name,
            )
        except Exception as exc:
            self._log(f"[bridge] platform account registration failed: {exc!r}")
        self._platform_cache[contact_id] = (person_id, account_id)
        return platform, account_id

    async def _human_delay(self) -> None:
        low, high = self.config.bot.human_delay_seconds
        if high <= 0:
            return
        await asyncio.sleep(low + (high - low) * self._rng())

    def _today(self) -> str:
        return self._now().strftime("%Y-%m-%d")

    def _in_quiet_hours(self) -> bool:
        window = self.config.bot.quiet_hours
        if not window:
            return False
        try:
            start = _to_minutes(window[0])
            end = _to_minutes(window[1])
        except ValueError:
            return False
        current = self._now()
        minutes = current.hour * 60 + current.minute
        if start == end:
            return False
        if start < end:
            return start <= minutes < end
        return minutes >= start or minutes < end


def _to_minutes(value: str) -> int:
    hours, minutes = value.split(":", 1)
    h, m = int(hours), int(minutes)
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(value)
    return h * 60 + m


def _event_from_row(row: dict) -> InboundEvent:
    """Rebuild the inbound message an outbox row is still waiting to answer."""
    return InboundEvent(
        contact_id=row["contact_id"],
        contact_name=row.get("contact_name") or "",
        text=row["text"],
        message_id=row["message_id"],
        is_group=bool(row.get("is_group")),
        timestamp=float(row.get("sent_at") or 0) or None,
    )
