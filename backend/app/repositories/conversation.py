import sqlite3
import uuid
from datetime import datetime, timezone

from app.core.sentinels import UNSET


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversationRepository:
    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        relationship_id: str | None,
        title: str | None,
        status: str,
    ) -> sqlite3.Row:
        conversation_id = str(uuid.uuid4())
        now = utc_now()

        conn.execute(
            """
            INSERT INTO conversations (
                id,
                user_id,
                person_id,
                relationship_id,
                title,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                user_id,
                person_id,
                relationship_id,
                title,
                status,
                now,
                now,
            ),
        )

        return conn.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ?
              AND user_id = ?
            """,
            (conversation_id, user_id),
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
                FROM conversations
                WHERE user_id = ?
                ORDER BY updated_at DESC, created_at DESC
                """,
                (user_id,),
            ).fetchall()

        return conn.execute(
            """
            SELECT *
            FROM conversations
            WHERE user_id = ?
              AND person_id = ?
            ORDER BY updated_at DESC, created_at DESC
            """,
            (user_id, person_id),
        ).fetchall()

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ?
              AND user_id = ?
            """,
            (conversation_id, user_id),
        ).fetchone()

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        relationship_id=UNSET,
        title=UNSET,
        status=UNSET,
    ) -> sqlite3.Row | None:
        existing = self.get(
            conn,
            user_id,
            conversation_id,
        )

        if existing is None:
            return None

        new_relationship_id = (
            existing["relationship_id"]
            if relationship_id is UNSET
            else relationship_id
        )

        new_title = (
            existing["title"]
            if title is UNSET
            else title
        )

        new_status = (
            existing["status"]
            if status is UNSET
            else status
        )

        conn.execute(
            """
            UPDATE conversations
            SET relationship_id = ?,
                title = ?,
                status = ?,
                updated_at = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                new_relationship_id,
                new_title,
                new_status,
                utc_now(),
                conversation_id,
                user_id,
            ),
        )

        return self.get(
            conn,
            user_id,
            conversation_id,
        )

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        cursor = conn.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
              AND user_id = ?
            """,
            (conversation_id, user_id),
        )

        return cursor.rowcount > 0
