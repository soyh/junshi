import sqlite3

from app.services.person_channel import (
    PersonChannelConflict,
    PersonChannelService,
    extract_wechat_id,
    looks_like_wechat_id,
)


def _conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE persons (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            nickname TEXT,
            notes TEXT,
            wechat_id TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            relationship_id TEXT,
            title TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            is_primary INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE person_platform_accounts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            account_handle TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            UNIQUE(user_id, platform, account_handle)
        );
        """
    )
    conn.execute("INSERT INTO persons (id, user_id, name) VALUES ('p1', 'u1', '小林')")
    conn.execute("INSERT INTO persons (id, user_id, name) VALUES ('p2', 'u1', '甜丶')")
    return conn


def test_the_same_person_keeps_one_conversation_across_channels():
    conn = _conn()
    service = PersonChannelService()

    first = service.link(conn, "u1", "p1", platform="xhs", handle="5f2c", display_name="小红书")
    second = service.link(conn, "u1", "p1", platform="soul", handle="888", display_name="Soul")

    assert first["person_id"] == second["person_id"] == "p1"
    xhs = service.resolve(conn, "u1", platform="xhs", handle="5f2c")
    soul = service.resolve(conn, "u1", platform="soul", handle="888")
    assert xhs["conversation_id"] == soul["conversation_id"]
    assert conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0] == 1


def test_resolve_is_scoped_to_the_signed_in_account():
    conn = _conn()
    PersonChannelService().link(conn, "u1", "p1", platform="xhs", handle="5f2c")
    service = PersonChannelService()

    assert service.resolve(conn, "u2", platform="xhs", handle="5f2c") is None
    assert service.resolve(conn, "u1", platform="soul", handle="5f2c") is None


def test_a_handle_never_silently_moves_to_another_person():
    conn = _conn()
    service = PersonChannelService()
    service.link(conn, "u1", "p1", platform="soul", handle="888")

    try:
        service.link(conn, "u1", "p2", platform="soul", handle="888")
    except PersonChannelConflict as exc:
        assert "小林" in str(exc)
    else:  # pragma: no cover - the guard is the point of the test
        raise AssertionError("a second person must not steal an existing handle")

    assert service.resolve(conn, "u1", platform="soul", handle="888")["person_id"] == "p1"

    moved = service.link(conn, "u1", "p2", platform="soul", handle="888", reassign=True)
    assert moved["person_id"] == "p2"
    assert conn.execute("SELECT COUNT(*) FROM person_platform_accounts").fetchone()[0] == 1


def test_wechat_ids_are_detected_but_ordinary_words_are_not():
    assert looks_like_wechat_id("lin_xiao-1996")
    assert extract_wechat_id("我微信 lin_xiao-1996 你加我") == "lin_xiao-1996"
    assert extract_wechat_id("微信号：abc12345") == "abc12345"
    assert extract_wechat_id("今天好累啊") == ""
    assert extract_wechat_id("wechat") == ""
    assert extract_wechat_id("哈哈哈") == ""


def test_capture_only_fills_an_empty_wechat_id():
    conn = _conn()
    service = PersonChannelService()

    assert service.capture_wechat_id(conn, "u1", "p1", "加我 lin_xiao96") == "lin_xiao96"
    assert service.capture_wechat_id(conn, "u1", "p1", "其实用 abc99887") == ""
    assert conn.execute("SELECT wechat_id FROM persons WHERE id = 'p1'").fetchone()[0] == "lin_xiao96"


def test_hand_typed_wechat_id_wins_over_capture():
    conn = _conn()
    service = PersonChannelService()
    service.set_wechat_id(conn, "u1", "p1", " typed_id_1 ")

    assert service.capture_wechat_id(conn, "u1", "p1", "加我 lin_xiao96") == ""
    assert conn.execute("SELECT wechat_id FROM persons WHERE id = 'p1'").fetchone()[0] == "typed_id_1"


def test_custom_alias_is_recognised_next_to_the_id():
    """A platform that censors 微信 makes people write "绿恐龙 xxxx"."""
    tokens = extract_wechat_id("绿恐龙 lin_xiao96", ["绿恐龙"])

    assert tokens == "lin_xiao96"


def test_alias_glued_to_the_id_still_yields_the_id():
    tokens = extract_wechat_id("V abc12345", ["V"])

    assert tokens == "abc12345"


def test_default_words_are_not_mistaken_for_ids():
    assert extract_wechat_id("微信 wechat VX") == ""
