"""Soul bubbles must map to stable ids: re-reading a chat never re-answers it."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.soul import SoulChannel  # noqa: E402


def _channel():
    channel = SoulChannel.__new__(SoulChannel)
    channel._seen = {}
    channel.events = []
    channel._handler = channel.events.append
    return channel


def _bubble(text, self_=False, time_="10:00"):
    return {"self": self_, "text": text, "time": time_, "sticker": False,
            "image": False, "image_url": ""}


def test_rereading_the_same_chat_does_not_emit_her_message_twice():
    channel = _channel()
    first = [_bubble("在吗")]
    channel._emit_new("小柯", first)
    assert [event.text for event in channel.events] == ["在吗"]

    # Our reply lands, the preview changes, the poll re-reads the same chat.
    # Her bubble must not repeat; our own bubble comes through as a self event
    # (the orchestrator uses it to cancel queued replies).
    second = first + [_bubble("在的", self_=True, time_="10:01")]
    channel._emit_new("小柯", second)
    assert [(event.text, event.is_self) for event in channel.events] == [
        ("在吗", False), ("在的", True),
    ]

    third = second + [_bubble("问你个事", time_="10:02")]
    channel._emit_new("小柯", third)
    assert [(event.text, event.is_self) for event in channel.events] == [
        ("在吗", False), ("在的", True), ("问你个事", False),
    ]


def test_one_minute_later_the_same_bubble_keeps_its_id():
    channel = _channel()
    bubble = [_bubble("晚安")]
    channel._emit_new("小柯", bubble)
    later = list(bubble)
    channel._emit_new("小柯", later)
    assert len(channel.events) == 1
    ids = {event.message_id for event in channel.events}
    assert len(ids) == 1


def test_identical_bubbles_at_different_positions_stay_distinct():
    channel = _channel()
    channel._emit_new("小柯", [_bubble("嗯"), _bubble("嗯"), _bubble("嗯")])
    assert len(channel.events) == 3
    assert len({event.message_id for event in channel.events}) == 3
