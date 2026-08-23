import sqlite3


class RelationshipStateRepository:
    def get_state(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> tuple[sqlite3.Row | None, sqlite3.Row | None, list[sqlite3.Row], list[sqlite3.Row]]:
        person = conn.execute(
            """
            SELECT *
            FROM persons
            WHERE id = ?
              AND user_id = ?
            """,
            (person_id, user_id),
        ).fetchone()

        if person is None:
            return None, None, [], []

        relationship = conn.execute(
            """
            SELECT *
            FROM relationships
            WHERE person_id = ?
              AND user_id = ?
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """,
            (person_id, user_id),
        ).fetchone()

        if relationship is None:
            return person, None, [], []

        interactions = conn.execute(
            """
            SELECT *
            FROM interactions
            WHERE person_id = ?
              AND relationship_id = ?
              AND user_id = ?
            ORDER BY occurred_at ASC, id ASC
            """,
            (person_id, relationship["id"], user_id),
        ).fetchall()

        messages = conn.execute(
            """
            SELECT m.*, c.person_id
            FROM messages AS m
            JOIN conversations AS c
              ON c.id = m.conversation_id
             AND c.user_id = m.user_id
            WHERE c.person_id = ?
              AND m.user_id = ?
            ORDER BY m.sent_at ASC, m.id ASC
            """,
            (person_id, user_id),
        ).fetchall()

        return person, relationship, list(messages), list(interactions)
