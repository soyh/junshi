import sqlite3

import pytest

from app.repositories.action_outcome import ActionOutcomeRepository


def test_action_outcome_database_rejects_duplicate_decision_id():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE action_outcomes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            decision_id TEXT NOT NULL,
            outcome TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE UNIQUE INDEX uq_action_outcomes_decision ON action_outcomes(decision_id)"
    )

    repository = ActionOutcomeRepository()
    repository.create(conn, "u1", "p1", "d1", "completed", "first")

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(conn, "u1", "p1", "d1", "failed", "duplicate")


def test_action_outcome_idempotency_is_per_decision_not_user_person_scope():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE action_outcomes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            decision_id TEXT NOT NULL,
            outcome TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE UNIQUE INDEX uq_action_outcomes_decision ON action_outcomes(decision_id)"
    )

    repository = ActionOutcomeRepository()
    repository.create(conn, "u1", "p1", "d1", "completed", "first")

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(conn, "u2", "p2", "d1", "completed", "cross-scope duplicate")
