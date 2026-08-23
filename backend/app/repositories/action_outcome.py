import sqlite3
import uuid
from datetime import datetime, timezone


class ActionOutcomeRepository:
    @staticmethod
    def list_for_person(conn: sqlite3.Connection, user_id: str, person_id: str) -> list[dict]:
        rows = conn.execute(
            """
            SELECT id, user_id, person_id, decision_id, outcome, note, created_at
            FROM action_outcomes
            WHERE user_id = ? AND person_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (user_id, person_id),
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def create(
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        decision_id: str,
        outcome: str,
        note: str | None,
    ) -> dict:
        item = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "person_id": person_id,
            "decision_id": decision_id,
            "outcome": outcome,
            "note": note,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        conn.execute(
            """
            INSERT INTO action_outcomes
                (id, user_id, person_id, decision_id, outcome, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(item.values()),
        )
        return item
