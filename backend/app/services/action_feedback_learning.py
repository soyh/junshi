import sqlite3

from app.services.action_feedback import ActionFeedbackService


class ActionFeedbackLearningService:
    def __init__(self, feedback_service: ActionFeedbackService | None = None):
        self.feedback_service = feedback_service or ActionFeedbackService()

    def get_learning_input(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.feedback_service.get_learning_context(conn, user_id, person_id)
        items = []
        for signal in context["signals"]:
            observed = signal["outcome_observed_count"] > 0
            items.append(
                {
                    "recommendation_id": signal["recommendation_id"],
                    "decision_count": signal["decision_count"],
                    "decision_counts": signal["decision_counts"],
                    "outcome_observed_count": signal["outcome_observed_count"],
                    "outcome_unknown_count": signal["outcome_unknown_count"],
                    "outcome_counts": signal["outcome_counts"],
                    "learning_status": "observed_feedback" if observed else "outcome_unknown",
                    "unknowns": ["recommendation_quality", "success", "relationship_impact"],
                    "source": {
                        "recommendation_id": signal["recommendation_id"],
                        "observed_outcomes": signal["outcome_observed_count"],
                        "unknown_outcomes": signal["outcome_unknown_count"],
                    },
                }
            )

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "learning_constraints": {
                "must_be_source_backed": True,
                "must_preserve_unknowns": True,
                "must_not_infer_recommendation_quality": True,
                "must_not_infer_success": True,
                "must_not_infer_relationship_impact": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
                "must_not_call_llm": True,
            },
            "items": items,
        }
