import sqlite3

from app.services.action_feedback_learning import ActionFeedbackLearningService


class ActionFeedbackLearningSynthesisService:
    def __init__(self, learning_service: ActionFeedbackLearningService | None = None):
        self.learning_service = learning_service or ActionFeedbackLearningService()

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        learning = self.learning_service.get_learning_input(conn, user_id, person_id)
        candidates = []
        for item in learning["items"]:
            observed = item["outcome_observed_count"] > 0
            candidates.append(
                {
                    "recommendation_id": item["recommendation_id"],
                    "learning_status": item["learning_status"],
                    "synthesis_status": "source_backed_candidate" if observed else "outcome_unknown",
                    "observed_outcome_count": item["outcome_observed_count"],
                    "outcome_counts": item["outcome_counts"],
                    "unknown_outcome_count": item["outcome_unknown_count"],
                    "unknowns": ["recommendation_quality", "success", "relationship_impact"],
                    "source": dict(item["source"]),
                }
            )

        return {
            "person": learning["person"],
            "relationship": learning["relationship"],
            "synthesis_constraints": {
                "must_be_source_backed": True,
                "must_preserve_unknowns": True,
                "must_not_infer_recommendation_quality": True,
                "must_not_infer_success": True,
                "must_not_infer_relationship_impact": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
                "must_not_call_llm": True,
            },
            "candidates": candidates,
        }
