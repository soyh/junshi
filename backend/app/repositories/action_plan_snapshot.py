import json
import sqlite3
import uuid
from datetime import datetime, timezone


class ActionPlanSnapshotRepository:
    @staticmethod
    def upsert(
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        recommendation: dict,
        action_plan: dict,
        evidence: list[dict],
    ) -> None:
        recommendation_id = recommendation["id"]
        conn.execute(
            """
            INSERT INTO action_plan_snapshots
                (id, user_id, person_id, recommendation_id,
                 recommendation_json, action_plan_json, evidence_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, person_id, recommendation_id) DO UPDATE SET
                recommendation_json = excluded.recommendation_json,
                action_plan_json = excluded.action_plan_json,
                evidence_json = excluded.evidence_json,
                created_at = excluded.created_at
            """,
            (
                str(uuid.uuid4()),
                user_id,
                person_id,
                recommendation_id,
                json.dumps(recommendation, ensure_ascii=False),
                json.dumps(action_plan, ensure_ascii=False),
                json.dumps(evidence, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    @staticmethod
    def list_for_person(
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> list[dict]:
        rows = conn.execute(
            """
            SELECT recommendation_json, action_plan_json, evidence_json, created_at
            FROM action_plan_snapshots
            WHERE user_id = ? AND person_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (user_id, person_id),
        ).fetchall()
        return [
            {
                "recommendation": json.loads(row[0]),
                "action_plan": json.loads(row[1]),
                "evidence": json.loads(row[2]),
                "created_at": row[3],
            }
            for row in rows
        ]
