import sys
from pathlib import Path

import pytest

import bridge_plugin as bp


@pytest.fixture
def plugin_home(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path


def test_config_roundtrip(plugin_home):
    path = bp.save_config(
        server="https://example.com",
        username="bridge_user",
        password="secret-password-123",
        channel="xhs",
        dry_run=False,
        daily_cap=25,
        quiet=("03:00", "05:30"),
        verify_tls=False,
    )
    assert path.is_file()
    summary = bp.load_config_summary()
    assert summary["server"] == "https://example.com"
    assert summary["username"] == "bridge_user"
    assert summary["channel"] == "xhs"
    assert summary["dry_run"] is False
    assert summary["daily_cap"] == 25
    assert summary["quiet"] == ("03:00", "05:30")
    assert summary["verify_tls"] is False


def test_config_rejects_unknown_channel(plugin_home):
    with pytest.raises(ValueError):
        bp.build_config("https://example.com", "u", "p", "telegram")


def test_status_lines_map_bridge_channel_names():
    lines = bp.status_lines(
        [
            {"channel": "wechatauto", "status": "online", "replies_today": 4, "updated_at": "now"},
            {"channel": "xhs", "status": "online", "replies_today": 0, "updated_at": "now"},
        ]
    )
    assert lines[0].startswith("微信：在线 · 今日回复 4")
    assert lines[1].startswith("小红书：在线 · 今日回复 0")
    assert lines[2] == "Soul：未上报"


def test_dev_command_uses_plugin_path():
    command, environment = bp.executable_command(Path("config.toml"))
    assert command[1:3] == ["-m", "lovebridge"]
    assert "plugins" in environment["PYTHONPATH"]
