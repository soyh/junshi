import sqlite3
import uuid
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MessageRepository:
    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        sender_type: str,
        content: str,
        sent_at: str | None,
    ) -> sqlite3.Row:
        message_id = str(uuid.uuid4())
        now = utc_now()
        actual_sent_at = sent_at if sent_at is not None else now

        conn.execute(
            """
            INSERT INTO messages (
                id,
                user_id,
                conversation_id,
                sender_type,
                content,
                sent_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                user_id,
                conversation_id,
                sender_type,
                content,
                actual_sent_at,
                now,
                now,
            ),
        )

        return conn.execute(
            """
            SELECT *
            FROM messages
            WHERE id = ?
              AND user_id = ?
            """,
            (message_id, user_id),
        ).fetchone()

    def list(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT *
            FROM messages
            WHERE user_id = ?
              AND conversation_id = ?
            ORDER BY sent_at ASC, created_at ASC
            """,
            (
                user_id,
                conversation_id,
            ),
        ).fetchall()

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM messages
            WHERE id = ?
              AND user_id = ?
            """,
            (
                message_id,
                user_id,
            ),
        ).fetchone()

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
    ) -> bool:
        cursor = conn.execute(
            """
            DELETE FROM messages
            WHERE id = ?
              AND user_id = ?
            """,
            (
                message_id,
                user_id,
            ),
        )

        return cursor.rowcount > 0
