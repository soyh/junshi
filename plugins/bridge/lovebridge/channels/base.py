"""Channel abstraction: anything that can deliver inbound messages and send text."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass
class InboundEvent:
    contact_id: str
    contact_name: str
    text: str
    message_id: str
    is_group: bool = False
    timestamp: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


Handler = Callable[[InboundEvent], None]


class Channel(Protocol):
    def set_handler(self, handler: Handler) -> None: ...

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def send(self, contact_id: str, text: str, is_group: bool = False) -> None: ...
