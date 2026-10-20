"""Reply orchestrator: dedup -> debounce -> record -> draft -> send -> record."""

from __future__ import annotations

import asyncio
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from .app_client import AppError, platform_of
from .channels.base import Channel, InboundEvent
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
        log: Callable[[str], None] = print,
        now: Callable[[], datetime] = datetime.now,
        rng: Callable[[], float] = random.random,
    ) -> None:
        self.config = config
        self.app = app
        self.channel = channel
        self.state = state
        self._log = log
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
        self._platform_cache: dict[str, tuple[str, str | None]] = {}

    # -- lifecycle --------------------------------------------------------
    async def run(self) -> None:
        self._loop = asyncio.get_running_loop()
        self.channel.set_handler(self._on_event)
        self._background = []
        try:
            await self.channel.start()
        except Exception as exc:
            self._log(f"[bridge] channel start failed: {exc!r}; will retry every 30s")
            self._background.append(asyncio.create_task(self._retry_start()))
        initial = await self._channel_status()
        if initial != "online":
            self._log(
                f"[bridge] channel not ready ({initial}); complete the platform login "
                "in the browser window the bridge opened"
            )
        self._background += [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._health_loop()),
        ]
        self._log(
            f"[bridge] started channel={self.config.channel.kind} "
            f"dry_run={self.config.bot.dry_run} app={self.config.app.base_url}"
        )
        await self._stop_event.wait()

    async def stop(self) -> None:
        self._stop_event.set()
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
                await self.channel.start()
            except Exception as exc:
                self._log(f"[bridge] channel start retry failed: {exc!r}")
                continue
            self._log("[bridge] channel started after retry")
            return

    async def _channel_status(self) -> str:
        """Report what the platform actually shows, not just that the process lives."""
        healthy = getattr(self.channel, "healthy", None)
        if healthy is None:
            return "online"
        try:
            return "online" if await healthy() else "未登录"
        except Exception:
            return "异常"

    async def _heartbeat_loop(self) -> None:
        while True:
            try:
                if self._heartbeat_enabled:
                    await self.app.heartbeat(
                        self.config.channel.kind,
                        await self._channel_status(),
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
            await asyncio.sleep(60)

    async def _health_loop(self) -> None:
        healthy = getattr(self.channel, "healthy", None)
        if healthy is None:
            return
        while True:
            await asyncio.sleep(60)
            try:
                ok = bool(await healthy())
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
                    self._log(f"[bridge] turn failed contact={contact_id}: {exc!r}")

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

        for event in events:
            await self.app.add_message_once(
                conversation_id,
                "person",
                event.text,
                operation_id=str(uuid.uuid5(uuid.NAMESPACE_URL, event.message_id)),
                sent_at=datetime.fromtimestamp(event.timestamp or time.time())
                .astimezone()
                .isoformat(timespec="seconds"),
                platform=platform,
                platform_account_id=account_id,
            )

        if self._in_quiet_hours():
            return TurnResult(contact_id, conversation_id, len(events), reason="quiet hours")

        if self.state.total_today(self._today()) >= bot.daily_reply_cap:
            return TurnResult(contact_id, conversation_id, len(events), reason="daily cap")

        context = await self.app.get_reply_context(conversation_id)
        reply = (context or {}).get("draft")
        reply = reply.strip() if isinstance(reply, str) else ""

        if not reply:
            return TurnResult(contact_id, conversation_id, len(events), reason="empty draft")
        if len(reply) > bot.max_reply_chars:
            return TurnResult(
                contact_id, conversation_id, len(events), reason=f"draft too long ({len(reply)})"
            )

        if bot.dry_run:
            self._log(f"[dry-run] draft for {contact_id}: {reply[:80]!r}")
            return TurnResult(contact_id, conversation_id, len(events), reply=reply, reason="dry run")

        await self._human_delay()
        await self.channel.send(contact_id, reply, is_group=bool(events[0].is_group))
        await self.app.add_message(conversation_id, "user", reply)
        count = self.state.bump(self._today(), contact_id)

        self._log(f"[bridge] replied to {contact_id} ({count} today): {reply[:60]!r}")
        return TurnResult(contact_id, conversation_id, len(events), reply=reply, sent=True)

    # -- helpers ----------------------------------------------------------
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
