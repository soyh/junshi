"""Personal WeChat channel via the open-source wxhook framework.

Requirements (important):
  * Windows, and WeChat **3.9.5.81** — that is the only version the open-source
    wxhook DLL targets. Newer 3.9.x / 4.x need the closed-source pywechat.
  * Run as the same user that is logged into WeChat; the framework launches
    WeChat with the DLL injected.
  * WeChat must already be logged in (or you log in on the window it opens).

The bot is started once; inbound text messages from private chats are forwarded
to the orchestrator, replies go through ``Bot.send_text``.
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid

from .base import Handler, InboundEvent


class WxhookChannel:
    def __init__(self, faked_version: str | None = None) -> None:
        self._faked_version = faked_version
        self._bot = None
        self._thread: threading.Thread | None = None
        self._handler: Handler | None = None
        self._self_wxid: str | None = None
        self._ready = threading.Event()

    def set_handler(self, handler: Handler) -> None:
        self._handler = handler

    async def start(self) -> None:
        self._bot = await asyncio.to_thread(self._create_bot)
        self._thread = threading.Thread(target=self._run_bot, daemon=True)
        self._thread.start()

    def _create_bot(self):
        try:
            from wxhook import Bot, events  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "wxhook is not installed. Run: pip install wxhook "
                "(Windows + WeChat 3.9.5.81 only)"
            ) from exc

        bot = Bot(
            faked_version=self._faked_version,
            on_start=lambda b: self._ready.set(),
        )

        @bot.handle(events.TEXT_MESSAGE)
        def _on_text(b: "Bot", event) -> None:  # noqa: ANN001
            self._dispatch(b, event)

        return bot

    def _run_bot(self) -> None:
        try:
            self._bot.run()
        except Exception:
            self._ready.clear()

    def _dispatch(self, bot, event) -> None:
        sender = str(getattr(event, "fromUser", "") or "")
        if not sender:
            return
        if self._self_wxid is None:
            try:
                self._self_wxid = bot.info.wxid
            except Exception:
                self._self_wxid = ""
        if sender == self._self_wxid:
            return
        if sender.endswith("@chatroom"):
            return  # groups are out of scope

        content = getattr(event, "content", None)
        if not isinstance(content, str) or not content.strip():
            return

        name = sender
        try:
            name = bot.get_contact(sender).nickname or sender
        except Exception:
            pass

        msg_id = getattr(event, "msgId", None)
        ts = getattr(event, "createTime", None)
        inbound = InboundEvent(
            contact_id=sender,
            contact_name=name,
            text=content,
            message_id=f"wxhook-{msg_id if msg_id is not None else uuid.uuid4().hex}",
            is_group=False,
            timestamp=float(ts) if ts else time.time(),
        )
        if self._handler:
            self._handler(inbound)

    async def stop(self) -> None:
        bot = self._bot
        if bot is None:
            return
        try:
            await asyncio.to_thread(bot.exit)
        except Exception:
            pass

    async def send(self, contact_id: str, text: str, is_group: bool = False) -> None:
        if self._bot is None:
            raise RuntimeError("wxhook channel is not started")
        response = await asyncio.to_thread(self._bot.send_text, contact_id, text)
        code = getattr(response, "code", None)
        if code not in (None, 200):
            raise RuntimeError(
                f"wxhook send_text failed: code={code} msg={getattr(response, 'msg', '')}"
            )
