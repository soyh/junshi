import sqlite3


class EvidenceRepository:
    def get_conversation_evidence(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> tuple[sqlite3.Row | None, list[sqlite3.Row], list[sqlite3.Row]]:
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
            return None, [], []

        messages = conn.execute(
            """
            SELECT *
            FROM messages
            WHERE conversation_id = ?
              AND user_id = ?
            ORDER BY sent_at ASC, created_at ASC, id ASC
            """,
            (conversation_id, user_id),
        ).fetchall()

        interactions = conn.execute(
            """
            SELECT *
            FROM interactions
            WHERE person_id = ?
              AND user_id = ?
            ORDER BY occurred_at ASC, created_at ASC, id ASC
            """,
            (conversation["person_id"], user_id),
        ).fetchall()

        return conversation, messages, interactions
