"""A reply the user types by hand must cancel ours, and feed the archive."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.base import InboundEvent  # noqa: E402
from test_outbox import CONTACT, _build, _event  # noqa: E402


class _App:
    def __init__(self, drafts=(), plan=None) -> None:
        self.drafts = list(drafts)
        self.plan = plan
        self.messages: list[tuple[str, str]] = []
        self.context_calls = 0

    async def find_or_create_person(self, name, contact_id, merge):  # noqa: ANN001
        return {"id": "person-1"}

    async def ensure_primary_conversation(self, person_id):  # noqa: ANN001
        return {"id": "conv-1"}

    async def ensure_scoped(self, conversation_id, person_id):  # noqa: ANN001
        return None

    async def ensure_platform_source(self, *args, **kwargs):  # noqa: ANN002
        return "plat-1"

    async def add_message_once(self, conversation_id, sender, text, **kwargs):  # noqa: ANN001
        self.messages.append((sender, text))

    async def add_message(self, conversation_id, sender, text, **kwargs):  # noqa: ANN001
        self.messages.append((sender, text))

    async def capture_wechat(self, person_id, text):  # noqa: ANN001
        return ""

    async def get_reply_context(self, conversation_id, rules="", self_profile=None, **kwargs):  # noqa: ANN001
        self.context_calls += 1
        draft = self.drafts.pop(0) if self.drafts else ""
        return {"draft": draft, "plan": self.plan}

    async def heartbeat(self, *args, **kwargs):  # noqa: ANN002
        return None


class _Channel:
    def __init__(self) -> None:
        self.sent: list[str] = []
        self.images: list[tuple[str, str]] = []

    def set_handler(self, handler) -> None:  # noqa: ANN001
        return None

    def set_logger(self, log) -> None:  # noqa: ANN001
        return None

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def status(self) -> str:
        return "online"

    async def send(self, contact_id, text, is_group=False) -> None:  # noqa: ANN001
        self.sent.append(text)

    async def send_image(self, contact_id, path, caption="") -> None:  # noqa: ANN001
        self.images.append((path, caption))


def _run(orchestrator, event) -> None:  # noqa: ANN001
    async def go() -> None:
        orchestrator._loop = asyncio.get_running_loop()
        orchestrator._accept(event)
        await asyncio.sleep(0.1)

    asyncio.run(go())


def test_a_manual_reply_cancels_the_queued_answer(tmp_path):
    app = _App(drafts=["我这边自己回"])
    channel = _Channel()
    orchestrator, state, logs = _build(tmp_path, app, channel)

    # A message still owes a reply (its turn failed earlier and was queued).
    state.enqueue("m1", CONTACT, "在吗", contact_name="小柯")
    assert state.outbox_pending(CONTACT)

    mine = InboundEvent(
        contact_id=CONTACT, contact_name="小柯", text="我自己回了，别插话",
        message_id="self-m2", is_self=True,
    )
    _run(orchestrator, mine)

    # Recorded as our own message (the style profile learns from it), never sent.
    assert ("user", "我自己回了，别插话") in app.messages
    assert state.outbox_pending(CONTACT) == []
    assert channel.sent == []
    assert any("手动回复" in line for line in logs)


def test_a_photo_tactic_sends_the_picture_instead_of_words(tmp_path):
    plan = {
        "read": "她要照片",
        "signal": "green",
        "send_allowed": True,
        "options": [
            {"tactic": "发一张", "why": "她明确要了", "line": "", "send": True,
             "photo_id": "photo-1", "source": "", "risk": ""},
        ],
    }
    app = _App(drafts=[""], plan=plan)
    channel = _Channel()

    async def fetch_photo(photo_id):  # noqa: ANN001
        assert photo_id == "photo-1"
        return b"\x89PNG\r\n\x1a\n", "image/png"

    app.fetch_photo = fetch_photo  # type: ignore[attr-defined]
    orchestrator, state, logs = _build(tmp_path, app, channel)
    _run(orchestrator, _event("m1"))

    assert [caption for _path, caption in channel.images] == [""]
    assert channel.sent == []
