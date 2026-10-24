"""Build 259: per-conversation manual takeover and batch chat intents."""

import sqlite3

import pytest

from app.services.analysis_strategic_reply import AnalysisStrategicReplyService, _taken_over
from app.services.conversation import ConversationNotFoundError, ConversationService
from app.services.relationship import RelationshipService

SCHEMA = """
CREATE TABLE users (id TEXT PRIMARY KEY);
CREATE TABLE persons (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT,
    nickname TEXT,
    notes TEXT
);
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT,
    relationship_id TEXT,
    title TEXT,
    status TEXT DEFAULT 'active',
    auto_reply_paused INTEGER NOT NULL DEFAULT 0,
    takeover_at TEXT,
    is_primary INTEGER NOT NULL DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    stage TEXT,
    status TEXT,
    current_goal TEXT,
    long_term_goal TEXT,
    notes TEXT,
    intent TEXT NOT NULL DEFAULT 'unsure',
    created_at TEXT,
    updated_at TEXT
);
"""


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.executescript(
        """
        INSERT INTO users VALUES ('u1'), ('u2');
        INSERT INTO persons VALUES ('p1', 'u1', '小林', NULL, NULL),
                                   ('p2', 'u1', '阿芝', NULL, NULL),
                                   ('p3', 'u2', '别人的人', NULL, NULL);
        INSERT INTO conversations VALUES
            ('c1', 'u1', 'p1', NULL, '小林', 'active', 0, NULL, 1, '2026-10-24', '2026-10-24'),
            ('c2', 'u1', 'p2', NULL, '阿芝', 'active', 0, NULL, 1, '2026-10-24', '2026-10-24'),
            ('c3', 'u2', 'p3', NULL, '别人的', 'active', 0, NULL, 1, '2026-10-24', '2026-10-24');
        """
    )
    return conn


def test_takeover_pauses_only_the_chosen_conversation():
    conn = _conn()
    service = ConversationService()

    row = service.set_takeover(conn, "u1", "c1", True)

    assert row["auto_reply_paused"] == 1
    assert row["takeover_at"] is not None
    other = service.get(conn, "u1", "c2")
    assert other["auto_reply_paused"] == 0


def test_takeover_can_be_released_and_other_users_stay_untouched():
    conn = _conn()
    service = ConversationService()
    service.set_takeover(conn, "u1", "c1", True)

    released = service.set_takeover(conn, "u1", "c1", False)
    assert released["auto_reply_paused"] == 0
    assert released["takeover_at"] is None

    with pytest.raises(ConversationNotFoundError):
        service.set_takeover(conn, "u1", "c3", True)
    assert service.get(conn, "u2", "c3")["auto_reply_paused"] == 0


def test_reply_generation_holds_while_takeover_is_on():
    conn = _conn()
    ConversationService().set_takeover(conn, "u1", "c1", True)
    assert _taken_over(conn, "u1", "c1") is True
    assert _taken_over(conn, "u1", "c2") is False


def test_takeover_flag_tolerates_an_old_conversation_table():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        "CREATE TABLE conversations (id TEXT PRIMARY KEY, user_id TEXT NOT NULL);"
        "INSERT INTO conversations VALUES ('c1', 'u1');"
    )

    assert _taken_over(conn, "u1", "c1") is False


def test_batch_intent_updates_many_people_at_once():
    conn = _conn()
    service = RelationshipService()

    rows = service.set_intent_many(conn, "u1", ["p1", "p2"], "long_term")

    assert len(rows) == 2
    assert {row["person_id"] for row in rows} == {"p1", "p2"}
    stored = {
        row["person_id"]: row["intent"]
        for row in conn.execute("SELECT person_id, intent FROM relationships WHERE user_id = 'u1'")
    }
    assert stored == {"p1": "long_term", "p2": "long_term"}


def test_batch_intent_leaves_other_accounts_alone():
    conn = _conn()

    rows = RelationshipService().set_intent_many(conn, "u1", ["p3"], "casual")

    assert rows == []
    assert conn.execute("SELECT COUNT(*) FROM relationships WHERE user_id = 'u2'").fetchone()[0] == 0
