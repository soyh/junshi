"""The outbox: a message that could not be answered is retried, never dropped."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.base import InboundEvent  # noqa: E402
from lovebridge.config import AppConfig, BotConfig, ChannelConfig, Config  # noqa: E402
from lovebridge.orchestrator import Orchestrator  # noqa: E402
from lovebridge.state import StateStore  # noqa: E402

CONTACT = "xhs:小柯"


class _App:
    def __init__(self, drafts, error: Exception | None = None, plan=None) -> None:
        self.drafts = list(drafts)
        self.error = error
        self.plan = plan
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
        return {"draft": draft, "plan": self.plan}

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


def test_plan_hold_skips_the_message_without_queueing_a_retry(tmp_path):
    app = _App(
        ["这条不该发出去"],
        plan={
            "send_allowed": False,
            "read": "她连发三条只回一个字，再追更糟",
            "options": [{"tactic": "先停", "send": False}],
        },
    )
    channel = _Channel()
    orchestrator, state, logs = _build(tmp_path, app, channel)

    _run(orchestrator, _event())

    counts = state.outbox_counts()
    assert channel.sent == []
    assert counts["skipped"] == 1 and counts["queued"] == 0
    assert any("hold" in line and "先停" in line for line in logs)
    assert "plan: hold" in state.last_failure()


def test_sendable_plan_still_sends_the_draft(tmp_path):
    app = _App(
        ["在，刚忙完"],
        plan={"send_allowed": True, "read": "正常", "options": [{"tactic": "顺着聊"}]},
    )
    channel = _Channel()
    orchestrator, _state, _logs = _build(tmp_path, app, channel)

    _run(orchestrator, _event())

    assert channel.sent == ["在，刚忙完"]


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


def test_daily_cap_long_wait_is_marked_failed_not_silently_deferred(tmp_path):
    """每日上限要等到明天（远超 3 分钟）时，直接显示成失败，别让用户干等。"""
    app = _App(["不该发出"])
    channel = _Channel()
    orchestrator, state, _logs = _build(tmp_path, app, channel, daily_reply_cap=0)

    _run(orchestrator, _event())

    assert state.outbox_pending(CONTACT) == []
    failed = state.outbox_rows("failed", limit=10)
    assert failed and "daily cap" in failed[0]["reason"]
    assert "3 分钟" in failed[0]["reason"]
    assert channel.sent == []


def test_quiet_hours_short_wait_stays_queued_then_fails_after_three_minutes(tmp_path):
    """安静时段前两次仍排队，等满 3 分钟还没发出去就转成失败。"""
    app = _App(["好"])
    channel = _Channel()
    orchestrator, state, _logs = _build(tmp_path, app, channel)
    orchestrator.LONG_WAIT_LIMIT = 180
    orchestrator.DEFER_SECONDS = 120

    row = {"created_at": orchestrator._now().isoformat(timespec="seconds")}
    assert orchestrator._waited_seconds([row]) < 1

    stale = {"created_at": (orchestrator._now() - timedelta(seconds=200)).isoformat(timespec="seconds")}
    assert orchestrator._waited_seconds([stale]) >= 180


def test_drain_skips_rows_that_were_already_answered(tmp_path):
    app = _App(["好"])
    channel = _Channel()
    orchestrator, state, _logs = _build(tmp_path, app, channel)
    state.enqueue("m1", CONTACT, "在吗")
    row = state.outbox_pending(CONTACT)[0]
    state.outbox_finish([int(row["id"])], "sent")

    assert asyncio.run(orchestrator.drain_outbox()) == 0
    assert channel.sent == []


def test_the_same_reply_is_never_sent_twice_to_one_contact(tmp_path):
    """Two turns for one moment (a re-read of the chat) must not answer twice."""
    app = _App(["行，那我今晚就去审判一下", "行，那我今晚就去审判一下"])
    channel = _Channel()
    orchestrator, state, logs = _build(tmp_path, app, channel)

    _run(orchestrator, _event("m1"))
    _run(orchestrator, _event("m2"))

    assert channel.sent == ["行，那我今晚就去审判一下"]
    assert any("duplicate" in line for line in logs)


def test_a_failed_send_releases_the_claim_so_the_retry_still_delivers(tmp_path):
    """Claiming happens before sending; a failure must hand the slot back."""
    app = _App(["好", "好"])
    channel = _Channel()
    orchestrator, state, _logs = _build(tmp_path, app, channel)
    calls = {"n": 0}

    async def flaky(contact_id, text, is_group=False):  # noqa: ANN001
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("editor lost focus")
        channel.sent.append(text)

    channel.send = flaky  # type: ignore[method-assign]

    _run(orchestrator, _event("m1"))
    assert channel.sent == []
    assert state.outbox_pending(CONTACT)

    row = state.outbox_pending(CONTACT)[0]
    state.outbox_finish([int(row["id"])], "queued", row["reason"], None)
    asyncio.run(orchestrator.drain_outbox())

    assert channel.sent == ["好"]


def test_recording_failure_after_delivery_does_not_trigger_a_resend(tmp_path):
    app = _App(["嗯嗯"])
    channel = _Channel()
    orchestrator, state, _logs = _build(tmp_path, app, channel)

    async def broken(*args, **kwargs):  # noqa: ANN002
        raise RuntimeError("HTTP 500 while recording")

    app.add_message = broken  # type: ignore[method-assign]

    _run(orchestrator, _event("m1"))

    assert channel.sent == ["嗯嗯"]
    assert state.outbox_pending(CONTACT) == []
