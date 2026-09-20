import sqlite3
import uuid
from datetime import datetime, timezone

from app.core.sentinels import UNSET


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RelationshipRepository:
    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        status: str,
        stage: str,
        long_term_goal: str | None,
        current_goal: str | None,
        notes: str | None,
    ) -> sqlite3.Row:
        relationship_id = str(uuid.uuid4())
        now = utc_now()

        conn.execute(
            """
            INSERT INTO relationships (
                id,
                user_id,
                person_id,
                status,
                stage,
                long_term_goal,
                current_goal,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                relationship_id,
                user_id,
                person_id,
                status,
                stage,
                long_term_goal,
                current_goal,
                notes,
                now,
                now,
            ),
        )

        return conn.execute(
            """
            SELECT *
            FROM relationships
            WHERE id = ?
              AND user_id = ?
            """,
            (relationship_id, user_id),
        ).fetchone()

    def list(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT *
            FROM relationships
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        relationship_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM relationships
            WHERE id = ?
              AND user_id = ?
            """,
            (relationship_id, user_id),
        ).fetchone()

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        relationship_id: str,
        status=UNSET,
        stage=UNSET,
        long_term_goal=UNSET,
        current_goal=UNSET,
        notes=UNSET,
    ) -> sqlite3.Row | None:
        existing = self.get(conn, user_id, relationship_id)

        if existing is None:
            return None

        new_status = existing["status"] if status is UNSET or status is None else status
        new_stage = existing["stage"] if stage is UNSET or stage is None else stage
        new_long_term_goal = (
            existing["long_term_goal"]
            if long_term_goal is UNSET
            else long_term_goal
        )
        new_current_goal = (
            existing["current_goal"]
            if current_goal is UNSET
            else current_goal
        )
        new_notes = existing["notes"] if notes is UNSET else notes

        conn.execute(
            """
            UPDATE relationships
            SET status = ?,
                stage = ?,
                long_term_goal = ?,
                current_goal = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                new_status,
                new_stage,
                new_long_term_goal,
                new_current_goal,
                new_notes,
                utc_now(),
                relationship_id,
                user_id,
            ),
        )

        return self.get(conn, user_id, relationship_id)

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        relationship_id: str,
    ) -> bool:
        cursor = conn.execute(
            """
            DELETE FROM relationships
            WHERE id = ?
              AND user_id = ?
            """,
            (relationship_id, user_id),
        )

        return cursor.rowcount > 0
