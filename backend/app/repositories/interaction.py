import sqlite3
import uuid
from datetime import datetime, timezone

from app.core.sentinels import UNSET


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InteractionRepository:
    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        relationship_id: str | None,
        interaction_type: str,
        occurred_at: str,
        content: str | None,
    ) -> sqlite3.Row:
        interaction_id = str(uuid.uuid4())
        now = utc_now()

        conn.execute(
            """
            INSERT INTO interactions (
                id,
                user_id,
                person_id,
                relationship_id,
                type,
                occurred_at,
                content,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                interaction_id,
                user_id,
                person_id,
                relationship_id,
                interaction_type,
                occurred_at,
                content,
                now,
                now,
            ),
        )

        return conn.execute(
            """
            SELECT *
            FROM interactions
            WHERE id = ?
              AND user_id = ?
            """,
            (interaction_id, user_id),
        ).fetchone()

    def list(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str | None = None,
    ) -> list[sqlite3.Row]:
        if person_id is None:
            return conn.execute(
                """
                SELECT *
                FROM interactions
                WHERE user_id = ?
                ORDER BY occurred_at DESC, created_at DESC
                """,
                (user_id,),
            ).fetchall()

        return conn.execute(
            """
            SELECT *
            FROM interactions
            WHERE user_id = ?
              AND person_id = ?
            ORDER BY occurred_at DESC, created_at DESC
            """,
            (user_id, person_id),
        ).fetchall()

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        interaction_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM interactions
            WHERE id = ?
              AND user_id = ?
            """,
            (interaction_id, user_id),
        ).fetchone()

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        interaction_id: str,
        relationship_id=UNSET,
        interaction_type=UNSET,
        occurred_at=UNSET,
        content=UNSET,
    ) -> sqlite3.Row | None:
        existing = self.get(
            conn,
            user_id,
            interaction_id,
        )

        if existing is None:
            return None

        new_relationship_id = (
            existing["relationship_id"]
            if relationship_id is UNSET
            else relationship_id
        )

        new_type = (
            existing["type"]
            if interaction_type is UNSET
            else interaction_type
        )

        new_occurred_at = (
            existing["occurred_at"]
            if occurred_at is UNSET
            else occurred_at
        )

        new_content = (
            existing["content"]
            if content is UNSET
            else content
        )

        conn.execute(
            """
            UPDATE interactions
            SET relationship_id = ?,
                type = ?,
                occurred_at = ?,
                content = ?,
                updated_at = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                new_relationship_id,
                new_type,
                new_occurred_at,
                new_content,
                utc_now(),
                interaction_id,
                user_id,
            ),
        )

        return self.get(
            conn,
            user_id,
            interaction_id,
        )

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        interaction_id: str,
    ) -> bool:
        cursor = conn.execute(
            """
            DELETE FROM interactions
            WHERE id = ?
              AND user_id = ?
            """,
            (interaction_id, user_id),
        )

        return cursor.rowcount > 0
