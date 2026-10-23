"""Build 255: the long-term archive folds new messages in without blocking replies."""

import json
import sqlite3

from app.api.routes.analysis_strategic_reply import (
    MEMORY_BATCH_TRIGGER,
    _memory_needs_refresh,
    _schedule_memory_refresh,
)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE persons (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT);
        CREATE TABLE conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            person_id TEXT,
            title TEXT
        );
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            sender TEXT,
            content TEXT
        );
        CREATE TABLE person_memories (
            person_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            summary_json TEXT,
            coverage_json TEXT,
            updated_at TEXT,
            PRIMARY KEY (person_id, user_id)
        );
        INSERT INTO persons VALUES ('p1', 'u1', '她');
        INSERT INTO conversations VALUES ('c1', 'u1', 'p1', '会话');
        """
    )
    return conn


def _messages(conn, count: int) -> None:
    for index in range(count):
        conn.execute(
            "INSERT INTO messages VALUES (?,?,?,?,?)",
            (f"m{index}", "c1", "u1", "person", f"第 {index} 条"),
        )


class _Background:
    def __init__(self) -> None:
        self.tasks = []

    def add_task(self, function, *args, **kwargs):
        self.tasks.append((function, args, kwargs))


def test_a_small_gap_does_not_spend_an_extra_model_call():
    conn = _conn()
    _messages(conn, MEMORY_BATCH_TRIGGER - 1)

    background = _Background()
    _schedule_memory_refresh(background, conn, "u1", "c1")

    assert background.tasks == []


def test_enough_new_messages_schedules_an_archive_refresh():
    conn = _conn()
    _messages(conn, MEMORY_BATCH_TRIGGER + 2)

    background = _Background()
    _schedule_memory_refresh(background, conn, "u1", "c1")

    assert len(background.tasks) == 1
    function, args, _ = background.tasks[0]
    assert function.__name__ == "background_refresh"
    assert args == ("u1", "p1")


def test_messages_already_folded_in_are_not_refolded():
    conn = _conn()
    _messages(conn, 10)
    coverage = {f"m{index}": "hash" for index in range(9)}
    conn.execute(
        "INSERT INTO person_memories VALUES (?,?,?,?,?)",
        ("p1", "u1", "{}", json.dumps(coverage), "now"),
    )

    assert _memory_needs_refresh(conn, "u1", "c1") == ("p1", False)


def test_a_corrupt_coverage_file_degrades_to_a_refresh():
    conn = _conn()
    _messages(conn, 8)
    conn.execute(
        "INSERT INTO person_memories VALUES (?,?,?,?,?)",
        ("p1", "u1", "{}", "not json", "now"),
    )

    person_id, behind = _memory_needs_refresh(conn, "u1", "c1")

    assert (person_id, behind) == ("p1", True)


def test_another_users_conversation_is_ignored():
    conn = _conn()
    _messages(conn, 10)

    assert _memory_needs_refresh(conn, "u2", "c1") == ("", False)
