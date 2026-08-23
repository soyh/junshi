import sqlite3


class AnalysisRepository:
    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> tuple[sqlite3.Row | None, sqlite3.Row | None, list[sqlite3.Row]]:
        conversation = conn.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ?
              AND user_id = ?
            """,
            (conversation_id, user_id),
        ).fetchone()

        if conversation is None:
            return None, None, []

        person = conn.execute(
            """
            SELECT *
            FROM persons
            WHERE id = ?
              AND user_id = ?
            """,
            (conversation["person_id"], user_id),
        ).fetchone()

        messages = conn.execute(
            """
            SELECT *
            FROM messages
            WHERE conversation_id = ?
              AND user_id = ?
            ORDER BY sent_at ASC, created_at ASC
            """,
            (conversation_id, user_id),
        ).fetchall()

        return conversation, person, messages
