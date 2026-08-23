import sqlite3


class TimelineRepository:
    def list_events(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        limit: int,
        offset: int,
    ) -> list[sqlite3.Row]:
        query = """
            SELECT *
            FROM (
                SELECT
                    i.id AS source_id,
                    'interaction' AS source_type,
                    i.user_id,
                    i.person_id,
                    i.type AS interaction_type,
                    i.occurred_at,
                    i.content,
                    NULL AS conversation_title,
                    NULL AS conversation_status,
                    NULL AS conversation_id,
                    NULL AS sender_type
                FROM interactions i
                WHERE i.user_id = ?
                  AND i.person_id = ?

                UNION ALL

                SELECT
                    c.id AS source_id,
                    'conversation' AS source_type,
                    c.user_id,
                    c.person_id,
                    NULL AS interaction_type,
                    c.created_at AS occurred_at,
                    NULL AS content,
                    c.title AS conversation_title,
                    c.status AS conversation_status,
                    NULL AS conversation_id,
                    NULL AS sender_type
                FROM conversations c
                WHERE c.user_id = ?
                  AND c.person_id = ?

                UNION ALL

                SELECT
                    m.id AS source_id,
                    'message' AS source_type,
                    m.user_id,
                    c.person_id,
                    NULL AS interaction_type,
                    m.sent_at AS occurred_at,
                    m.content,
                    NULL AS conversation_title,
                    NULL AS conversation_status,
                    m.conversation_id,
                    m.sender_type
                FROM messages m
                JOIN conversations c
                  ON c.id = m.conversation_id
                 AND c.user_id = m.user_id
                WHERE m.user_id = ?
                  AND c.person_id = ?
            )
            ORDER BY datetime(occurred_at) DESC, source_type ASC, source_id ASC
            LIMIT ? OFFSET ?
        """

        return conn.execute(
            query,
            (
                user_id,
                person_id,
                user_id,
                person_id,
                user_id,
                person_id,
                limit,
                offset,
            ),
        ).fetchall()

    def count_events(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> int:
        query = """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM interactions i
                    WHERE i.user_id = ?
                      AND i.person_id = ?
                )
                +
                (
                    SELECT COUNT(*)
                    FROM conversations c
                    WHERE c.user_id = ?
                      AND c.person_id = ?
                )
                +
                (
                    SELECT COUNT(*)
                    FROM messages m
                    JOIN conversations c
                      ON c.id = m.conversation_id
                     AND c.user_id = m.user_id
                    WHERE m.user_id = ?
                      AND c.person_id = ?
                ) AS total
        """

        row = conn.execute(
            query,
            (
                user_id,
                person_id,
                user_id,
                person_id,
                user_id,
                person_id,
            ),
        ).fetchone()

        return int(row["total"])
