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


def _write_snapshot(profile_id, status, updated_at, replies=0):
    import json

    bp.status_path(profile_id).write_text(
        json.dumps({"status": status, "updated_at": updated_at, "replies_today": replies}),
        encoding="utf-8",
    )


def _mark_alive(profile_id):
    import os

    bp.pid_path(profile_id).write_text(str(os.getpid()), encoding="ascii")


def test_local_status_reads_profile_snapshot(plugin_home):
    from datetime import datetime

    profile_id = bp.create_profile(
        name="小红书A",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="xhs",
    )
    _mark_alive(profile_id)
    _write_snapshot(profile_id, "online", datetime.now().isoformat(timespec="seconds"), 3)
    detail = bp.local_status(profile_id)
    assert detail["running"] is True
    assert detail["status"] == "在线"
    assert detail["replies_today"] == 3


def test_local_status_flags_stale_heartbeat_and_stopped_profile(plugin_home):
    from datetime import datetime, timedelta

    running = bp.create_profile("xhs-a")
    _mark_alive(running)
    stale = (datetime.now() - timedelta(minutes=10)).isoformat(timespec="seconds")
    _write_snapshot(running, "online", stale)
    assert bp.local_status(running)["status"] == "无响应（心跳过期）"

    stopped = bp.create_profile("xhs-b")
    _write_snapshot(stopped, "online", datetime.now().isoformat(timespec="seconds"))
    assert bp.local_status(stopped)["status"] == "未运行"


def test_local_status_surfaces_retries_and_failures(plugin_home):
    import json
    from datetime import datetime

    profile_id = bp.create_profile(
        name="小红书C", server="https://example.com", username="u",
        password="password-123456", channel="xhs",
    )
    _mark_alive(profile_id)
    bp.status_path(profile_id).write_text(
        json.dumps({
            "status": "online",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "replies_today": 1,
            "outbox": {"queued": 2, "failed": 1, "skipped": 0, "sent": 1},
            "error": "xhs:小柯: RemoteProtocolError",
        }),
        encoding="utf-8",
    )

    detail = bp.local_status(profile_id)
    assert detail["status"] == "在线 · 待重试 2 · 1 条未发出"
    assert detail["queued"] == 2 and detail["failed"] == 1
    assert "RemoteProtocolError" in detail["error"]

    line = bp.status_lines([{"id": profile_id, "name": "小红书C", "channel": "xhs"}])[0]
    assert "待重试 2" in line and "1 条未发出" in line
    assert "RemoteProtocolError" in line


def test_status_lines_keep_profiles_of_the_same_platform_apart(plugin_home):
    from datetime import datetime

    now = datetime.now().isoformat(timespec="seconds")
    first = bp.create_profile(
        name="小红书A", server="https://example.com", username="u",
        password="password-123456", channel="xhs",
    )
    second = bp.create_profile(
        name="小红书B", server="https://example.com", username="u",
        password="password-123456", channel="xhs",
    )
    for profile_id in (first, second):
        _mark_alive(profile_id)
    _write_snapshot(first, "online", now, 3)
    _write_snapshot(second, "未登录", now)
    lines = bp.status_lines(bp.list_profiles())
    assert len(lines) == 2
    joined = "\n".join(lines)
    assert "小红书｜小红书A：在线 · 今日回复 3" in joined
    assert "小红书｜小红书B：未登录" in joined


def test_status_lines_when_empty():
    assert bp.status_lines([]) == ["尚未创建通道：点「新建通道」为每个平台各建一个。"]


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



def test_reply_rules_round_trip_per_profile(plugin_home):
    rules = "称呼对方“小满”，每次不超过两句，不用问句收尾。"
    profile_id = bp.create_profile(
        name="小红书通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="xhs",
        rules=rules,
    )
    item = {row["id"]: row for row in bp.list_profiles()}[profile_id]
    assert item["rules"] == rules
    text = bp.config_path(profile_id).read_text(encoding="utf-8")
    assert "rules = " in text


def test_reply_rules_default_to_empty_and_are_optional(plugin_home):
    text = bp.build_config("x", "https://example.com", "u", "password-123456", "wechat")
    assert 'rules = ""' in text
    profile_id = bp.create_profile(
        name="微信通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="wechat",
    )
    assert {row["id"]: row for row in bp.list_profiles()}[profile_id]["rules"] == ""


def test_person_facts_come_from_the_shared_settings(plugin_home):
    """本人信息是全局的：录一次，所有通道的配置和界面都用这一份。"""
    bp.save_global(person={"nickname": "阿哲", "city": "杭州"})
    profile_id = bp.create_profile(
        name="微信通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="wechat",
    )
    item = {row["id"]: row for row in bp.list_profiles()}[profile_id]
    assert item["person"] == {"nickname": "阿哲", "city": "杭州"}
    text = bp.config_path(profile_id).read_text(encoding="utf-8")
    assert "[person]" in text and 'nickname = "阿哲"' in text

    # 没填就是空，不写进配置，也不编造
    bp.save_global(person={}, rules="")
    blank = bp.create_profile(
        name="空通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="soul",
    )
    assert "[person]" not in bp.config_path(blank).read_text(encoding="utf-8")
    assert {row["id"]: row for row in bp.list_profiles()}[blank]["person"] == {}


def test_outbox_lines_surface_pending_work(plugin_home, monkeypatch):
    profile_id = bp.create_profile(
        name="小红书通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="xhs",
    )
    items = bp.list_profiles()

    monkeypatch.setattr(
        bp,
        "local_status",
        lambda pid: {
            "state": "在线", "queued": 2, "failed": 1, "error": "Server disconnected",
            "running": True, "raw": "online",
        },
    )
    lines = bp.outbox_lines(items)
    assert any("待重试 2 条" in line and "未发出 1 条" in line for line in lines)
    assert any("Server disconnected" in line for line in lines)

    monkeypatch.setattr(
        bp,
        "local_status",
        lambda pid: {
            "state": "在线", "queued": 0, "failed": 0, "error": "",
            "running": True, "raw": "online",
        },
    )
    assert "暂无待发或失败的消息" in bp.outbox_lines(items)[0]


def test_retry_outbox_reports_daemon_answer(plugin_home, monkeypatch):
    profile_id = bp.create_profile(
        name="微信通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="wechat",
    )

    class Done:
        stdout = "resent 2 message(s)\n"
        stderr = ""

    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        return Done()

    monkeypatch.setattr(bp.subprocess, "run", fake_run)
    assert bp.retry_outbox(profile_id) == "resent 2 message(s)"
    assert "outbox" in seen["command"] and "--retry" in seen["command"]


def test_global_settings_are_shared_and_survive_profile_creation(plugin_home):
    assert bp.load_global() == {"person": {}, "rules": ""}
    bp.save_global(person={"nickname": "小满", "city": "杭州", "unused": "x"}, rules="短句、口语")
    shared = bp.load_global()
    assert shared["person"] == {"nickname": "小满", "city": "杭州"}
    assert shared["rules"] == "短句、口语"

    profile_id = bp.create_profile(
        name="微信通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="wechat",
    )
    item = bp.summary(profile_id)
    assert item["person"]["nickname"] == "小满"
    # 通道自己没写规则时继承全局默认规则
    assert item["rules"] == "短句、口语"
    assert "小满" in bp.config_path(profile_id).read_text(encoding="utf-8")


def test_channel_rules_override_the_global_default(plugin_home):
    bp.save_global(person={"nickname": "小满"}, rules="全局默认")
    profile_id = bp.create_profile(
        name="小红书通道",
        server="https://example.com",
        username="u",
        password="password-123456",
        channel="xhs",
        rules="本通道专用规则",
    )
    item = bp.summary(profile_id)
    assert item["rules"] == "本通道专用规则"
    assert bp.load_global()["rules"] == "全局默认"
