"""A log line must never be able to kill the bridge."""

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge import console  # noqa: E402


class GbkConsole(io.TextIOBase):
    """Mimics a Chinese Windows console: only GBK characters can be printed."""

    encoding = "gbk"

    def __init__(self):
        self.buffer = io.BytesIO()

    def write(self, text):
        text.encode("gbk")  # raises UnicodeEncodeError for emoji, like the real thing
        return len(text)

    def flush(self):
        return None


def test_write_line_survives_unencodable_text(monkeypatch):
    fake = GbkConsole()
    monkeypatch.setattr(sys, "stdout", fake)
    console.write_line("[soul] 会话：小明🌾 已回复")
    assert "小明".encode("utf-8") in fake.buffer.getvalue()


def test_write_line_ignores_missing_stdout(monkeypatch):
    monkeypatch.setattr(sys, "stdout", None)
    console.write_line("no crash without a console")


def test_write_line_uses_plain_print_when_possible(monkeypatch, capsys):
    console.write_line("plain line")
    assert "plain line" in capsys.readouterr().out


def test_channels_accept_the_orchestrator_logger():
    from lovebridge.channels.soul import SoulChannel
    from lovebridge.channels.xhs import XhsChannel

    seen = []
    for channel in (SoulChannel(profile_dir="/tmp/none"), XhsChannel(profile_dir="/tmp/none")):
        channel.set_logger(seen.append)
        channel._logged("hello")
    assert seen == ["hello", "hello"]
