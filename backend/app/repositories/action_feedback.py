import sqlite3


class ActionFeedbackRepository:
    @staticmethod
    def list_for_person(conn: sqlite3.Connection, user_id: str, person_id: str) -> list[dict]:
        rows = conn.execute(
            """
            SELECT
                d.id AS decision_id,
                d.recommendation_id,
                d.decision,
                d.note AS decision_note,
                d.created_at AS decision_created_at,
                o.id AS outcome_id,
                o.outcome,
                o.note AS outcome_note,
                o.created_at AS outcome_created_at
            FROM action_decisions d
            LEFT JOIN action_outcomes o
              ON o.decision_id = d.id
             AND o.user_id = d.user_id
             AND o.person_id = d.person_id
            WHERE d.user_id = ? AND d.person_id = ?
            ORDER BY d.created_at DESC, d.id DESC, o.created_at DESC, o.id DESC
            """,
            (user_id, person_id),
        ).fetchall()
        return [dict(row) for row in rows]
