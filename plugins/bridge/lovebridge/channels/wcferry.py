"""Experimental direct adapter for personal WeChat via WeChatFerry (wcferry).

This only works on Windows with a specific pinned WeChat version and the
wcferry service injected. It is version-locked and carries a real ban risk for
the WeChat account that runs it. Prefer the webhook channel if your bridge is
already running elsewhere.
"""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime

from .base import Handler, InboundEvent


class WcferryChannel:
    def __init__(self, poll_interval: float = 0.2) -> None:
        self._poll = float(poll_interval)
        self._handler: Handler | None = None
        self._wcf = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._self_wxid: str | None = None

    def set_handler(self, handler: Handler) -> None:
        self._handler = handler

    async def start(self) -> None:
        try:
            from wcferry import Wcf  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "wcferry is not installed. Run: pip install wcferry "
                "(Windows only, and only with the matching WeChat version)"
            ) from exc

        self._wcf = Wcf()
        if not self._wcf.is_login():
            raise RuntimeError("WeChat is not logged in on this machine")
        self._self_wxid = self._wcf.get_self_wxid()
        self._wcf.enable_receiving_msg()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    async def stop(self) -> None:
        self._running = False
        if self._wcf is not None:
            try:
                self._wcf.disable_receiving_msg()
            except Exception:
                pass

    def _loop(self) -> None:
        from queue import Empty

        while self._running and self._wcf is not None:
            try:
                message = self._wcf.get_msg()
            except Empty:
                time.sleep(self._poll)
                continue
            except Exception:
                self._running = False
                break

            if not self._running:
                break
            try:
                self._dispatch(message)
            except Exception:
                continue

    def _dispatch(self, message) -> None:
        # Text messages only; 1 == MSG_TYPE_TEXT in wcferry.
        if getattr(message, "type", None) != 1:
            return
        sender = str(getattr(message, "sender", "") or "")
        if not sender or sender == self._self_wxid:
            return
        if getattr(message, "is_self", lambda: False)():
            return

        room_id = str(getattr(message, "roomid", "") or "")
        if room_id:
            contact_id, is_group = room_id, True
            try:
                name = self._wcf.get_room_name(room_id) or room_id
            except Exception:
                name = room_id
        else:
            contact_id, is_group = sender, False
            try:
                name = self._wcf.get_contact(sender).get("name") or sender
            except Exception:
                name = sender

        text = str(getattr(message, "content", "") or "").strip()
        if not text:
            return

        ts = float(getattr(message, "ts", time.time()))
        event = InboundEvent(
            contact_id=contact_id,
            contact_name=name,
            text=text,
            message_id=f"wc-{getattr(message, 'id', uuid.uuid4().hex)}",
            is_group=is_group,
            timestamp=ts,
        )
        if self._handler:
            self._handler(event)

    async def send(self, contact_id: str, text: str, is_group: bool = False) -> None:
        if self._wcf is None:
            raise RuntimeError("wcferry channel is not started")
        if not self._wcf.send_text(text, contact_id):
            raise RuntimeError(f"wcferry send_text failed for {contact_id}")
