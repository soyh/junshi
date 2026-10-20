"""Interactive mock channel for local testing.

Type lines in the console:
    wxid_abc<TAB>她：在干嘛呀
    wxid_abc<TAB>她：周末有空吗

Replies are printed, nothing is sent anywhere.
"""

from __future__ import annotations

import asyncio
import sys
import threading
import time
import uuid

from .base import Handler, InboundEvent


class MockChannel:
    def __init__(self) -> None:
        self._handler: Handler | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def set_handler(self, handler: Handler) -> None:
        self._handler = handler

    async def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._read_stdin, daemon=True)
        self._thread.start()

    async def stop(self) -> None:
        self._running = False

    def _read_stdin(self) -> None:
        for line in sys.stdin:
            if not self._running:
                break
            line = line.rstrip("\r\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                print("[mock] format: contact_id<TAB>text")
                continue
            contact_id, text = parts[0].strip(), parts[1]
            name = parts[2].strip() if len(parts) > 2 else contact_id
            event = InboundEvent(
                contact_id=contact_id,
                contact_name=name,
                text=text,
                message_id=f"mock-{uuid.uuid4().hex}",
                timestamp=time.time(),
            )
            if self._handler:
                self._handler(event)

    async def send(self, contact_id: str, text: str, is_group: bool = False) -> None:
        await asyncio.sleep(0)
        print(f"[mock -> {contact_id}] {text}")
