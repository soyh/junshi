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

    # Canonical full-history reader. Keep this unbounded for analysis/evidence.
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

    # Presentation-only reader. Fetch newest N efficiently, then return them in
    # chronological order so the UI still reads like a normal conversation.
    def list_window(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        limit: int,
        from_time: str | None = None,
        to_time: str | None = None,
        before: str | None = None,
    ) -> list[sqlite3.Row]:
        conditions = ["user_id = ?", "conversation_id = ?"]
        params: list[object] = [user_id, conversation_id]
        if from_time is not None:
            conditions.append("sent_at >= ?")
            params.append(from_time)
        if to_time is not None:
            conditions.append("sent_at <= ?")
            params.append(to_time)
        if before is not None:
            conditions.append("sent_at < ?")
            params.append(before)
        params.append(limit)
        where_clause = " AND ".join(conditions)
        return conn.execute(
            f"""
            SELECT *
            FROM (
                SELECT *
                FROM messages
                WHERE {where_clause}
                ORDER BY sent_at DESC, created_at DESC
                LIMIT ?
            )
            ORDER BY sent_at ASC, created_at ASC
            """,
            params,
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

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
        values: dict[str, str],
    ) -> sqlite3.Row | None:
        allowed = {"sender_type", "content", "sent_at"}
        updates = [(key, value) for key, value in values.items() if key in allowed]
        if not updates:
            return self.get(conn, user_id, message_id)
        assignments = ", ".join(f"{key} = ?" for key, _ in updates)
        params: list[object] = [value for _, value in updates]
        params.extend([utc_now(), message_id, user_id])
        cursor = conn.execute(
            f"""
            UPDATE messages
            SET {assignments}, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            params,
        )
        if cursor.rowcount == 0:
            return None
        return self.get(conn, user_id, message_id)

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
