"""Status reporting: the panel must show login state, not just process liveness."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.soul import SoulChannel  # noqa: E402
from lovebridge.channels.xhs import XhsChannel  # noqa: E402
from lovebridge.orchestrator import Orchestrator  # noqa: E402


class _Locator:
    def __init__(self, count: int) -> None:
        self._count = count

    async def count(self) -> int:
        return self._count


class _XhsPage:
    def __init__(self, conversations: int, login: bool) -> None:
        self.conversations = conversations
        self.login = login

    def locator(self, selector: str) -> _Locator:
        return _Locator(self.conversations if "conv-list" in selector else 0)

    async def evaluate(self, script: str):
        return self.login


class _SoulPage:
    def __init__(self, conversations: int, text: str, sync: bool = False) -> None:
        self.conversations = conversations
        self.text = text
        self.sync = sync

    def locator(self, selector: str) -> _Locator:
        if selector == ".conv-list":
            return _Locator(self.conversations)
        if selector == ".sync-scrim":
            return _Locator(1 if self.sync else 0)
        return _Locator(0)

    async def evaluate(self, script: str):
        return self.text


def test_xhs_status_reads_login_wall() -> None:
    channel = XhsChannel(profile_dir=Path("/tmp/unused-xhs"))
    channel._page = _XhsPage(conversations=0, login=True)
    assert asyncio.run(channel.status()) == "未登录"

    channel._page = _XhsPage(conversations=3, login=False)
    assert asyncio.run(channel.status()) == "online"


def test_soul_status_reads_login_wall() -> None:
    channel = SoulChannel(profile_dir=Path("/tmp/unused-soul"))
    channel._page = _SoulPage(conversations=0, text="打开 Soul App，扫描下方二维码\n扫码登录")
    assert asyncio.run(channel.status()) == "未登录"

    channel._page = _SoulPage(conversations=2, text="消息")
    assert asyncio.run(channel.status()) == "online"

    channel._page = _SoulPage(conversations=0, text="消息", sync=True)
    assert asyncio.run(channel.status()) == "已登录·待同步"


class _SlowChannel:
    def __init__(self) -> None:
        self.started = False

    def set_handler(self, handler) -> None:  # noqa: ANN001
        self.handler = handler

    async def start(self) -> None:
        await asyncio.sleep(0.2)
        self.started = True

    async def status(self) -> str:
        return "online" if self.started else "未登录"

    async def stop(self) -> None:
        return None


class _FakeApp:
    def __init__(self) -> None:
        self.reports: list[str] = []

    async def heartbeat(self, channel: str, status: str, replies: int, detail: str = "") -> None:
        self.reports.append(status)


def test_heartbeat_reports_starting_before_channel_ready() -> None:
    app = _FakeApp()
    config = SimpleNamespace(
        channel=SimpleNamespace(kind="xhs"),
        bot=SimpleNamespace(dry_run=True, max_concurrency=2),
        app=SimpleNamespace(base_url="http://test"),
        source_path=Path("/tmp/unused/bridge/config.toml"),
    )
    state = SimpleNamespace(total_today=lambda day: 0)
    orchestrator = Orchestrator(config, app, _SlowChannel(), state, log=lambda *_: None)

    async def run() -> None:
        task = asyncio.create_task(orchestrator.run())
        await asyncio.sleep(0.05)
        await orchestrator.stop()
        await task

    asyncio.run(run())
    assert app.reports and app.reports[0] == "启动中"
    assert "online" in app.reports
