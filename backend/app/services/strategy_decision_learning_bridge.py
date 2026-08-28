import sqlite3

from app.services.strategy_decision_learning import StrategyDecisionLearningService


class StrategyDecisionLearningBridgeService:
    """Expose strategy-decision learning input to the broader learning-strategy layer."""

    def __init__(self, learning_service=None):
        self.learning_service = learning_service or StrategyDecisionLearningService()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        learning = self.learning_service.get_learning_input(conn, user_id, person_id)
        return {
            "items": learning["items"],
            "learning_constraints": {
                **learning["learning_constraints"],
                "source_backed": True,
                "read_only": True,
            },
        }

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        learning = self.learning_service.get_learning_input(conn, user_id, person_id)
        observed = [item for item in learning["items"] if item["learning_eligible"]]
        unknown = [item for item in learning["items"] if not item["learning_eligible"]]
        counts = {}
        for item in observed:
            recommendation_id = item["recommendation_id"]
            counts[recommendation_id] = counts.get(recommendation_id, 0) + 1

        return {
            "learning_candidate_decision_ids": [item["decision_id"] for item in observed],
            "unknown_decision_ids": [item["decision_id"] for item in unknown],
            "recommendation_observed_counts": counts,
            "learning_candidate_count": len(observed),
            "unknown_count": len(unknown),
            "constraints": {
                "read_only": True,
                "source_backed_only": True,
                "must_preserve_source_provenance": True,
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
