import sqlite3

from app.services.strategy_decision_lifecycle import StrategyDecisionLifecycleService


class StrategyDecisionLearningService:
    """Build source-backed learning input from the decision lifecycle."""

    def __init__(self, lifecycle_service=None):
        self.lifecycle_service = lifecycle_service or StrategyDecisionLifecycleService()

    def get_learning_input(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.lifecycle_service.get_context(conn, user_id, person_id)
        items = []

        for lifecycle_item in context["lifecycle"]:
            decision = lifecycle_item["decision"]
            feedback = lifecycle_item["feedback"]
            outcome = decision.get("outcome")
            observed = lifecycle_item["feedback_status"] == "outcome_observed"
            unknowns = (
                feedback.get("unknowns")
                if feedback is not None and feedback.get("unknowns") is not None
                else ["action_effect", "relationship_impact"]
            )

            items.append(
                {
                    "decision_id": lifecycle_item["decision_id"],
                    "recommendation_id": decision["recommendation_id"],
                    "decision_status": decision["decision"],
                    "result_status": lifecycle_item["result_status"],
                    "feedback_status": lifecycle_item["feedback_status"],
                    "learning_status": "observed_feedback" if observed else "outcome_unknown",
                    "learning_eligible": observed,
                    "outcome": outcome,
                    "feedback": feedback,
                    "unknowns": unknowns,
                    "source": {
                        "decision_id": lifecycle_item["decision_id"],
                        "recommendation_id": decision["recommendation_id"],
                        "outcome_id": outcome["id"] if outcome else None,
                        "feedback_status": lifecycle_item["feedback_status"],
                    },
                }
            )

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "items": items,
            "learning_constraints": {
                "source_backed": True,
                "must_preserve_unknowns": True,
                "must_not_infer_recommendation_quality": True,
                "must_not_infer_success": True,
                "must_not_infer_relationship_impact": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
                "must_not_auto_send": True,
                "must_not_call_llm": True,
            },
        }
