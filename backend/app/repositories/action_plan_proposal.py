import json
import sqlite3
import uuid
from datetime import datetime, timezone


class ActionPlanProposalRepository:
    @staticmethod
    def create(
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        recommendation_id: str,
        action: str,
        evidence_source_ids: list[str],
        priority: str | None = None,
        time_horizon: str | None = None,
    ) -> dict:
        item = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "person_id": person_id,
            "recommendation_id": recommendation_id,
            "action": action,
            "evidence_source_ids": list(evidence_source_ids),
            "priority": priority,
            "time_horizon": time_horizon,
            "status": "proposed",
            "requires_user_confirmation": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        conn.execute(
            """
            INSERT INTO action_plan_proposals
                (
                    id, user_id, person_id, recommendation_id, action,
                    evidence_source_ids, priority, time_horizon, status,
                    requires_user_confirmation, created_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["id"],
                item["user_id"],
                item["person_id"],
                item["recommendation_id"],
                item["action"],
                json.dumps(item["evidence_source_ids"], ensure_ascii=False),
                item["priority"],
                item["time_horizon"],
                item["status"],
                int(item["requires_user_confirmation"]),
                item["created_at"],
            ),
        )
        return item

    @staticmethod
    def get_available_by_recommendation(
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        recommendation_id: str,
    ) -> dict | None:
        row = conn.execute(
            """
            SELECT
                id, user_id, person_id, recommendation_id, action,
                evidence_source_ids, priority, time_horizon, status,
                requires_user_confirmation, created_at
            FROM action_plan_proposals
            WHERE user_id = ?
              AND person_id = ?
              AND recommendation_id = ?
              AND status = 'proposed'
              AND requires_user_confirmation = 1
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (user_id, person_id, recommendation_id),
        ).fetchone()
        if row is None:
            return None

        item = dict(row)
        item["evidence_source_ids"] = json.loads(item["evidence_source_ids"])
        item["requires_user_confirmation"] = bool(item["requires_user_confirmation"])
        return item
