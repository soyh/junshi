import sqlite3
import uuid
from datetime import datetime, timezone


class ActionExecutionRepository:
    @staticmethod
    def list_for_person(conn: sqlite3.Connection, user_id: str, person_id: str) -> list[dict]:
        rows = conn.execute(
            """
            SELECT id, user_id, person_id, decision_id, executed_at, note, created_at
            FROM action_executions
            WHERE user_id = ? AND person_id = ?
            ORDER BY executed_at DESC, id DESC
            """,
            (user_id, person_id),
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_decision(conn: sqlite3.Connection, user_id: str, person_id: str, decision_id: str) -> dict | None:
        row = conn.execute(
            """
            SELECT id, user_id, person_id, decision_id, executed_at, note, created_at
            FROM action_executions
            WHERE decision_id = ? AND user_id = ? AND person_id = ?
            """,
            (decision_id, user_id, person_id),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        decision_id: str,
        executed_at: str | None,
        note: str | None,
    ) -> dict:
        timestamp = executed_at or datetime.now(timezone.utc).isoformat()
        item = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "person_id": person_id,
            "decision_id": decision_id,
            "executed_at": timestamp,
            "note": note,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        conn.execute(
            """
            INSERT INTO action_executions
                (id, user_id, person_id, decision_id, executed_at, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(item.values()),
        )
        return item
