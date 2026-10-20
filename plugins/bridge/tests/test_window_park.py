"""Parking the browser window: hide after login, reveal when login is needed."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge import window  # noqa: E402
from lovebridge.channels.soul import SoulChannel  # noqa: E402
from lovebridge.channels.xhs import XhsChannel  # noqa: E402


class _Locator:
    def __init__(self, count: int) -> None:
        self._count = count

    async def count(self) -> int:
        return self._count


class _Page:
    def __init__(self, conversations: int = 1, login: bool = False) -> None:
        self.conversations = conversations
        self.login = login

    def locator(self, selector: str) -> _Locator:
        return _Locator(self.conversations if "conv-list" in selector else 0)

    async def evaluate(self, script: str):
        return self.login

    async def bring_to_front(self) -> None:
        return None


class _Recorder:
    def __init__(self) -> None:
        self.hides: list[tuple[dict, str]] = []
        self.shows: list[dict] = []

    def hide(self, roots, **kwargs):  # noqa: ANN001
        self.hides.append((kwargs, kwargs.get("mode", "")))
        return 1

    def show(self, roots, **kwargs):  # noqa: ANN001
        self.shows.append(kwargs)
        return 1


def _channel(cls, **kwargs):  # noqa: ANN001
    channel = cls(profile_dir=Path("C:/tmp/profile"), **kwargs)
    channel._headed = True
    channel._page = _Page()
    return channel


def test_hide_after_login_in_headless_mode(monkeypatch) -> None:  # noqa: ANN001
    recorder = _Recorder()
    import lovebridge.channels.xhs as xhs_module

    monkeypatch.setattr(xhs_module, "window", recorder)
    channel = _channel(XhsChannel, headless=True)
    asyncio.run(channel._park_if_logged_in())
    assert channel._parked is True
    assert recorder.hides and recorder.hides[0][1] == "hide"


def test_minimize_mode_is_passed_through(monkeypatch) -> None:  # noqa: ANN001
    recorder = _Recorder()
    import lovebridge.channels.xhs as xhs_module

    monkeypatch.setattr(xhs_module, "window", recorder)
    channel = _channel(XhsChannel, headless=True, window_mode="minimize")
    asyncio.run(channel._park_if_logged_in())
    assert recorder.hides[0][1] == "minimize"


def test_visible_mode_keeps_the_window(monkeypatch) -> None:  # noqa: ANN001
    recorder = _Recorder()
    import lovebridge.channels.soul as soul_module

    monkeypatch.setattr(soul_module, "window", recorder)
    # Explicit "show" and a non-headless config both leave the window alone.
    channel = _channel(SoulChannel, headless=True, window_mode="show")
    asyncio.run(channel._park_if_logged_in())
    assert recorder.hides == []

    channel = _channel(SoulChannel, headless=False)
    asyncio.run(channel._park_if_logged_in())
    assert recorder.hides == []


def test_login_wall_brings_the_window_back(monkeypatch) -> None:  # noqa: ANN001
    recorder = _Recorder()
    import lovebridge.channels.soul as soul_module

    monkeypatch.setattr(soul_module, "window", recorder)
    channel = _channel(SoulChannel, headless=True)
    channel._parked = True
    channel._page = _Page(conversations=0, login=True)
    asyncio.run(channel._reveal_window())
    assert recorder.shows and channel._parked is False


def test_descendants_finds_child_processes() -> None:
    if sys.platform != "win32":
        return
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
    try:
        deadline = time.time() + 8
        found: set[int] = set()
        while time.time() < deadline and child.pid not in found:
            found = window.descendants(os.getpid())
            time.sleep(0.2)
        assert child.pid in found
    finally:
        child.kill()


def test_hidden_window_record_roundtrip(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    window._remember("xhs:C:/tmp/p", [11, 22])
    assert window.remembered("xhs:C:/tmp/p") == [11, 22]
