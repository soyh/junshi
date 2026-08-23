import sqlite3
import uuid
from datetime import datetime, timezone


class ActionDecisionRepository:
    @staticmethod
    def list_for_person(conn: sqlite3.Connection, user_id: str, person_id: str) -> list[dict]:
        rows = conn.execute(
            """
            SELECT id, user_id, person_id, recommendation_id, decision, note, created_at
            FROM action_decisions
            WHERE user_id = ? AND person_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (user_id, person_id),
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get(conn: sqlite3.Connection, user_id: str, person_id: str, decision_id: str) -> dict | None:
        row = conn.execute(
            """
            SELECT id, user_id, person_id, recommendation_id, decision, note, created_at
            FROM action_decisions
            WHERE id = ? AND user_id = ? AND person_id = ?
            """,
            (decision_id, user_id, person_id),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        recommendation_id: str | None,
        decision: str,
        note: str | None,
    ) -> dict:
        item = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "person_id": person_id,
            "recommendation_id": recommendation_id,
            "decision": decision,
            "note": note,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        conn.execute(
            """
            INSERT INTO action_decisions
                (id, user_id, person_id, recommendation_id, decision, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(item.values()),
        )
        return item
