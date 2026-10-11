import sqlite3
import uuid

from app.services.memory_update import MemoryUpdateService


class MemorySynthesisService:
    def __init__(self, memory_update_service: MemoryUpdateService | None = None):
        self.memory_update_service = memory_update_service or MemoryUpdateService()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.memory_update_service.get_context(conn, user_id, person_id)
        updates = []

        for candidate in context["candidates"]:
            outcome = candidate["content"]["outcome"]
            update_id = str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"memory-update:{candidate['id']}")
            )
            updates.append(
                {
                    "id": update_id,
                    "status": "proposed",
                    "category": "action_feedback",
                    "source_candidate_id": candidate["id"],
                    "source_decision_id": candidate["source_decision_id"],
                    "source_outcome_id": candidate["source_outcome_id"],
                    "source_created_at": candidate["source_created_at"],
                    "memory": {
                        "action_outcome": outcome,
                        "note": candidate["content"]["note"],
                    },
                    "unknowns": [
                        "long_term_relationship_impact",
                        "future_behavior_after_this_outcome",
                    ],
                }
            )

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "memory_constraints": {
                **context["memory_constraints"],
                "must_not_infer_relationship_impact": True,
                "must_preserve_unknowns": True,
            },
            "updates": updates,
        }
