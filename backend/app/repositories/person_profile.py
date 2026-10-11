import sqlite3


class PersonProfileRepository:
    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM persons
            WHERE id = ?
              AND user_id = ?
            """,
            (person_id, user_id),
        ).fetchone()

    def list_relationships(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT *
            FROM relationships
            WHERE user_id = ?
              AND person_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (user_id, person_id),
        ).fetchall()

    def get_statistics(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> sqlite3.Row:
        return conn.execute(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM relationships
                    WHERE user_id = ?
                      AND person_id = ?
                ) AS relationship_count,
                (
                    SELECT COUNT(*)
                    FROM conversations
                    WHERE user_id = ?
                      AND person_id = ?
                ) AS conversation_count,
                (
                    SELECT COUNT(*)
                    FROM interactions
                    WHERE user_id = ?
                      AND person_id = ?
                ) AS interaction_count,
                (
                    SELECT COUNT(*)
                    FROM messages AS m
                    INNER JOIN conversations AS c
                        ON c.id = m.conversation_id
                    WHERE m.user_id = ?
                      AND c.user_id = ?
                      AND c.person_id = ?
                ) AS message_count
            """,
            (
                user_id,
                person_id,
                user_id,
                person_id,
                user_id,
                person_id,
                user_id,
                user_id,
                person_id,
            ),
        ).fetchone()

    def get_latest_interaction(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM interactions
            WHERE user_id = ?
              AND person_id = ?
            ORDER BY occurred_at DESC, created_at DESC, id DESC
            LIMIT 1
            """,
            (user_id, person_id),
        ).fetchone()
