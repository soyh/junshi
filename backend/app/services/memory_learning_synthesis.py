import sqlite3

from app.services.action_feedback import ActionFeedbackService
from app.services.memory_synthesis import MemorySynthesisService


class MemoryLearningSynthesisService:
    def __init__(
        self,
        memory_synthesis_service: MemorySynthesisService | None = None,
        feedback_service: ActionFeedbackService | None = None,
    ):
        self.memory_synthesis_service = memory_synthesis_service or MemorySynthesisService()
        self.feedback_service = feedback_service or ActionFeedbackService()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        memory = self.memory_synthesis_service.get_context(conn, user_id, person_id)
        feedback = self.feedback_service.get_context(conn, user_id, person_id)
        signals = self.feedback_service.get_signals(conn, user_id, person_id)["signals"]

        feedback_by_outcome = {
            item.get("outcome_id"): item
            for item in feedback["feedback"]
            if item.get("outcome_id")
        }
        signals_by_recommendation = {
            item.get("recommendation_id"): item for item in signals
        }

        updates = []
        for update in memory["updates"]:
            source = feedback_by_outcome.get(update["source_outcome_id"])
            recommendation_id = source.get("recommendation_id") if source else None
            signal = signals_by_recommendation.get(recommendation_id)
            updates.append(
                {
                    **update,
                    "learning_provenance": {
                        "status": "observed_outcome" if source else "source_unresolved",
                        "recommendation_id": recommendation_id,
                        "source_decision_id": update["source_decision_id"],
                        "source_outcome_id": update["source_outcome_id"],
                        "outcome_observed_count": signal["outcome_observed_count"] if signal else 0,
                        "outcome_unknown_count": signal["outcome_unknown_count"] if signal else 0,
                        "outcome_counts": signal["outcome_counts"] if signal else {},
                    },
                }
            )

        return {
            "person": memory["person"],
            "relationship": memory["relationship"],
            "memory_constraints": {
                **memory["memory_constraints"],
                "must_preserve_learning_provenance": True,
                "must_not_infer_recommendation_quality": True,
                "must_not_infer_success": True,
                "must_not_infer_relationship_impact": True,
                "must_not_auto_persist": True,
            },
            "updates": updates,
        }
