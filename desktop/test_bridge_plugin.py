from pathlib import Path

import pytest

import bridge_plugin as bp


@pytest.fixture
def plugin_home(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path


def test_profile_config_roundtrip(plugin_home):
    profile_id = bp.create_profile("工作微信")
    path = bp.save_profile(
        profile_id,
        name="工作微信",
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
    text = path.read_text(encoding="utf-8")
    assert "[channel.xhs]" in text
    assert "browser" in text

    items = bp.list_profiles()
    assert len(items) == 1
    item = items[0]
    assert item["id"] == profile_id
    assert item["name"] == "工作微信"
    assert item["server"] == "https://example.com"
    assert item["channel"] == "xhs"
    assert item["dry_run"] is False
    assert item["daily_cap"] == 25
    assert item["quiet"] == ("03:00", "05:30")
    assert item["verify_tls"] is False
    assert item["running"] is False


def test_multiple_profiles_are_independent(plugin_home):
    first = bp.create_profile("微信")
    second = bp.create_profile("小红书")
    for profile_id, channel in ((first, "wechat"), (second, "xhs")):
        bp.save_profile(
            profile_id,
            name=channel,
            server="https://example.com",
            username=f"user_{channel}",
            password="password-123456",
            channel=channel,
        )
    items = {item["id"]: item for item in bp.list_profiles()}
    assert set(items) == {first, second}
    assert items[first]["channel"] == "wechat"
    assert items[second]["channel"] == "xhs"
    assert bp.config_path(first) != bp.config_path(second)


def test_legacy_single_config_is_migrated(plugin_home):
    legacy = bp.plugin_dir() / "config.toml"
    legacy.write_text(
        '[app]\nbase_url = "https://example.com"\nusername = "old"\npassword = "old-password-123"\n',
        encoding="utf-8",
    )
    items = bp.list_profiles()
    assert [item["id"] for item in items] == ["default"]
    assert not legacy.exists()
    assert items[0]["username"] == "old"


def test_config_rejects_unknown_channel(plugin_home):
    with pytest.raises(ValueError):
        bp.build_config("x", "https://example.com", "u", "p", "telegram")


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


def test_status_lines_show_login_failure_and_stale_heartbeat():
    from datetime import datetime, timedelta, timezone

    fresh = datetime.now(timezone.utc).isoformat()
    stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    lines = bp.status_lines(
        [
            {"channel": "xhs", "status": "未登录", "replies_today": 0, "updated_at": fresh},
            {"channel": "soul", "status": "online", "replies_today": 2, "updated_at": stale},
        ]
    )
    assert lines[0] == "微信：未上报"
    assert lines[1].startswith("小红书：未登录")
    assert lines[2].startswith("Soul：离线")


def test_dev_command_uses_plugin_path(plugin_home):
    profile_id = bp.create_profile("dev")
    bp.save_profile(
        profile_id,
        name="dev",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="wechat",
    )
    command, environment = bp.executable_command(profile_id)
    assert command[1:3] == ["-m", "lovebridge"]
    assert "plugins" in environment["PYTHONPATH"]
    assert command[-1] == "run"


def test_create_profile_writes_config_immediately(plugin_home):
    profile_id = bp.create_profile(
        name="小红书通道",
        server="https://example.com",
        username="bridge_user",
        password="password-123456",
        channel="xhs",
    )
    assert bp.config_path(profile_id).is_file()
    items = bp.list_profiles()
    assert [item["id"] for item in items] == [profile_id]
    assert items[0]["name"] == "小红书通道"
    assert items[0]["channel"] == "xhs"
    assert items[0]["headless"] is True


def test_two_platforms_keep_separate_profiles_and_browser_dirs(plugin_home):
    first = bp.create_profile(
        name="小红书通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="xhs",
    )
    second = bp.create_profile(
        name="Soul通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="soul",
    )
    items = {item["id"]: item for item in bp.list_profiles()}
    assert set(items) == {first, second}
    assert items[first]["channel"] == "xhs"
    assert items[second]["channel"] == "soul"
    text_first = bp.config_path(first).read_text(encoding="utf-8").replace("\\\\", "/")
    text_second = bp.config_path(second).read_text(encoding="utf-8").replace("\\\\", "/")
    assert "browser/xhs" in text_first
    assert "browser/soul" in text_second
    assert "headless = true" in text_first and "headless = true" in text_second


def test_headless_can_be_turned_off(plugin_home):
    text = bp.build_config(
        "x", "https://example.com", "u", "password-123456", "xhs",
        browser_dir="C:/tmp/browser", headless=False,
    )
    assert "headless = false" in text

