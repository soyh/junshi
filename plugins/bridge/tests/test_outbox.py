"""The outbox: a message that could not be answered is retried, never dropped."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.base import InboundEvent  # noqa: E402
from lovebridge.config import AppConfig, BotConfig, ChannelConfig, Config  # noqa: E402
from lovebridge.orchestrator import Orchestrator  # noqa: E402
from lovebridge.state import StateStore  # noqa: E402

CONTACT = "xhs:小柯"


class _App:
    def __init__(self, drafts, error: Exception | None = None) -> None:
        self.drafts = list(drafts)
        self.error = error
        self.context_calls = 0
        self.messages = []

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

    async def get_reply_context(self, conversation_id, rules="", self_profile=None):  # noqa: ANN001
        self.context_calls += 1
        self.last_profile = self_profile
        if self.error is not None:
            raise self.error
        draft = self.drafts.pop(0) if self.drafts else ""
        return {"draft": draft}

    async def heartbeat(self, *args, **kwargs):  # noqa: ANN002
        return None


class _Channel:
    def __init__(self) -> None:
        self.sent: list[str] = []
        self.handler = None

    def set_handler(self, handler) -> None:  # noqa: ANN001
        self.handler = handler

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


def _config(tmp_path: Path, **bot) -> Config:
    state = tmp_path / "state.sqlite3"
    defaults = dict(
        dry_run=False,
        debounce_seconds=0.0,
        human_delay_seconds=(0.0, 0.0),
        max_concurrency=1,
        state_path=state,
    )
    defaults.update(bot)
    return Config(
        app=AppConfig(base_url="http://test", username="u", password="p"),
        bot=BotConfig(**defaults),
        channel=ChannelConfig(kind="xhs"),
        source_path=tmp_path / "config.toml",
    )


def _event(message_id: str = "m1") -> InboundEvent:
    return InboundEvent(
        contact_id=CONTACT, contact_name="小柯", text="在吗", message_id=message_id
    )


def _build(tmp_path, app, channel, **bot):  # noqa: ANN001
    config = _config(tmp_path, **bot)
    state = StateStore(config.bot.state_path)
    logs: list[str] = []
    orchestrator = Orchestrator(config, app, channel, state, log=logs.append)
    return orchestrator, state, logs


def _run(orchestrator, event) -> None:  # noqa: ANN001
    async def go() -> None:
        orchestrator._loop = asyncio.get_running_loop()
        orchestrator._accept(event)
        await asyncio.sleep(0.1)

    asyncio.run(go())


def test_failed_turn_is_kept_and_retried_until_it_sends(tmp_path):
    app = _App(["好的，我在"], error=RuntimeError("Server disconnected"))
    channel = _Channel()
    orchestrator, state, logs = _build(tmp_path, app, channel)

    _run(orchestrator, _event())
    rows = state.outbox_pending(CONTACT)
    assert len(rows) == 1 and rows[0]["attempts"] == 1
    assert rows[0]["next_at"] and channel.sent == []
    assert any("retry" in line for line in logs)

    app.error = None
    state.outbox_finish([int(rows[0]["id"])], "queued", rows[0]["reason"], None)
    asyncio.run(orchestrator.drain_outbox())

    assert channel.sent == ["好的，我在"]
    assert state.outbox_pending(CONTACT) == []
    assert state.outbox_counts()["sent"] == 1


def test_unsendable_draft_is_skipped_with_a_visible_reason(tmp_path):
    app = _App([""])
    channel = _Channel()
    orchestrator, state, logs = _build(tmp_path, app, channel)

    _run(orchestrator, _event())

    counts = state.outbox_counts()
    assert counts["skipped"] == 1 and counts["queued"] == 0
    assert channel.sent == []
    assert any("skip" in line and "empty draft" in line for line in logs)
    assert "empty draft" in state.last_failure()


def test_failure_is_reported_in_status_after_max_attempts(tmp_path):
    app = _App([])
    channel = _Channel()
    orchestrator, state, _logs = _build(tmp_path, app, channel)
    state.enqueue("m1", CONTACT, "在吗")

    row = state.outbox_pending(CONTACT)[0]
    for attempt in range(1, Orchestrator.MAX_ATTEMPTS + 1):
        orchestrator._finish_outbox(CONTACT, [_event()], error=f"boom {attempt}")

    counts = state.outbox_counts()
    assert counts["failed"] == 1 and counts["queued"] == 0
    assert "boom" in state.last_failure()

    orchestrator._write_status("online")
    payload = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert payload["outbox"]["failed"] == 1
    assert "boom" in payload["error"]


def test_quiet_hours_defers_without_burning_attempts(tmp_path):
    app = _App(["不该发出"])
    channel = _Channel()
    orchestrator, state, _logs = _build(
        tmp_path, app, channel, quiet_hours=("00:00", "23:59")
    )

    _run(orchestrator, _event())

    rows = state.outbox_pending(CONTACT)
    assert len(rows) == 1, "quiet hours must keep the message"
    assert rows[0]["attempts"] == 0, "deferral is not a failure"
    assert rows[0]["reason"] == "quiet hours"
    assert channel.sent == []


def test_daily_cap_defers_to_the_next_day(tmp_path):
    app = _App(["不该发出"])
    channel = _Channel()
    orchestrator, state, _logs = _build(tmp_path, app, channel, daily_reply_cap=0)

    _run(orchestrator, _event())

    rows = state.outbox_pending(CONTACT)
    assert len(rows) == 1 and rows[0]["reason"] == "daily cap"
    assert channel.sent == []


def test_drain_skips_rows_that_were_already_answered(tmp_path):
    app = _App(["好"])
    channel = _Channel()
    orchestrator, state, _logs = _build(tmp_path, app, channel)
    state.enqueue("m1", CONTACT, "在吗")
    row = state.outbox_pending(CONTACT)[0]
    state.outbox_finish([int(row["id"])], "sent")

    assert asyncio.run(orchestrator.drain_outbox()) == 0
    assert channel.sent == []
