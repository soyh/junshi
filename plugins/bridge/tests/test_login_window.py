"""Login-wall handling of the browser channels (Soul / Xiaohongshu).

Soul and Xiaohongshu keep their conversation shell mounted behind the login
overlay, so "the list exists" is not proof of a valid session. These tests pin
the order of the checks: the login wall wins, and the window is brought back
when it is parked.
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.soul import SoulChannel
from lovebridge.channels.xhs import XhsChannel


class FakeLocator:
    def __init__(self, count=0):
        self._count = count

    async def count(self):
        return self._count

    async def click(self, **_kwargs):
        return None

    @property
    def first(self):
        return self


class FakePage:
    def __init__(self, counts=None, text="", login=False):
        self.counts = counts or {}
        self.text = text
        self.login = login
        self.front = 0

    def locator(self, selector):
        selector = str(selector)
        for marker, count in self.counts.items():
            if marker in selector:
                return FakeLocator(count)
        return FakeLocator(0)

    async def evaluate(self, script, arg=None):
        if "login-container" in script or "login-modal" in script or "qr" in script.lower():
            return self.login
        return self.text

    async def bring_to_front(self):
        self.front += 1


def test_soul_status_prefers_login_wall_over_mounted_list():
    channel = SoulChannel(profile_dir=".")
    channel._page = FakePage(
        counts={".conv-list": 1, ".conversation": 0},
        text="扫码登录 手机号登录",
    )

    assert asyncio.run(channel.status()) == "未登录"


def test_soul_status_is_online_without_login_wall():
    channel = SoulChannel(profile_dir=".")
    channel._page = FakePage(counts={".conv-list": 1}, text="消息 选择一段对话")

    assert asyncio.run(channel.status()) == "online"


def test_xhs_status_prefers_login_wall_over_mounted_list():
    channel = XhsChannel(profile_dir=".")
    channel._page = FakePage(counts={".xhs-im-conv-list": 1}, login=True)

    assert asyncio.run(channel.status()) == "未登录"


def test_xhs_status_is_online_without_login_wall():
    channel = XhsChannel(profile_dir=".")
    channel._page = FakePage(counts={".xhs-im-conv-list": 1}, login=False)

    assert asyncio.run(channel.status()) == "online"


@pytest.mark.parametrize("factory", [SoulChannel, XhsChannel])
def test_parked_window_is_revealed_when_login_wall_shows(monkeypatch, factory):
    channel = factory(profile_dir=".")
    channel._page = FakePage(login=True)
    channel._parked = True
    channel._warned_login = True
    calls = []
    monkeypatch.setattr(
        "lovebridge.channels.soul.window.show",
        lambda *a, **k: calls.append("soul") or 1,
        raising=False,
    )
    monkeypatch.setattr(
        "lovebridge.channels.xhs.window.show",
        lambda *a, **k: calls.append("xhs") or 1,
        raising=False,
    )

    asyncio.run(channel._need_login("检测到未登录"))

    assert calls, "a parked browser must be brought back for the login wall"
    assert channel._parked is False
    assert channel._page.front == 1


@pytest.mark.parametrize("factory", [SoulChannel, XhsChannel])
def test_start_always_launches_a_visible_window(monkeypatch, factory):
    channel = factory(profile_dir=".")
    launched = []

    async def fake_launch(headless):
        launched.append(headless)

    async def fake_ensure():
        return None

    async def fake_mark():
        return None

    async def fake_park():
        return None

    async def fake_status():
        return "未登录"

    async def fake_baseline():
        return None

    channel._launch = fake_launch
    channel._ensure_chat = fake_ensure
    channel._ensure_list = fake_ensure
    channel._maybe_mark_logged_in = fake_mark
    channel._park_if_logged_in = fake_park
    channel.status = fake_status
    channel._baseline = fake_baseline
    monkeypatch.setattr(channel, "_pw", object())

    asyncio.run(channel.start())

    assert launched == [False], "the first launch must be a real window"
