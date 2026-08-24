import sqlite3
import uuid

from app.services.action_feedback import ActionFeedbackService


class MemoryUpdateService:
    def __init__(self, feedback_service: ActionFeedbackService | None = None):
        self.feedback_service = feedback_service or ActionFeedbackService()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.feedback_service.get_context(conn, user_id, person_id)
        candidates = []
        for item in context["feedback"]:
            if not item.get("outcome_id") or not item.get("outcome"):
                continue
            candidates.append(
                {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"memory:{item['decision_id']}:{item['outcome_id']}")),
                    "status": "proposed",
                    "category": "action_feedback",
                    "content": {
                        "decision": item["decision"],
                        "outcome": item["outcome"],
                        "note": item["outcome_note"],
                    },
                    "source_decision_id": item["decision_id"],
                    "source_outcome_id": item["outcome_id"],
                    "source_created_at": item["outcome_created_at"],
                }
            )

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "memory_constraints": {
                "must_be_source_backed": True,
                "must_be_proposed": True,
                "must_preserve_unknowns": True,
                "must_not_infer_from_missing_outcome": True,
                "must_not_auto_persist": True,
                "must_not_change_relationship": True,
                "must_have_stable_source_identity": True,
            },
            "candidates": candidates,
        }
