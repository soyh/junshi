import sqlite3

from app.services.strategy_decision_learning import StrategyDecisionLearningService


class StrategyDecisionLearningSynthesisService:
    """Synthesize strategy decision learning candidates without mutating data."""

    def __init__(self, learning_service=None):
        self.learning_service = learning_service or StrategyDecisionLearningService()

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        learning = self.learning_service.get_learning_input(conn, user_id, person_id)
        items = learning["items"]

        observed = [item for item in items if item["learning_eligible"]]
        unknown = [item for item in items if not item["learning_eligible"]]

        recommendation_counts = {}
        for item in observed:
            recommendation_id = item["recommendation_id"]
            recommendation_counts[recommendation_id] = recommendation_counts.get(recommendation_id, 0) + 1

        return {
            "person": learning["person"],
            "relationship": learning["relationship"],
            "learning_items": items,
            "learning_candidate_decision_ids": [item["decision_id"] for item in observed],
            "unknown_decision_ids": [item["decision_id"] for item in unknown],
            "recommendation_observed_counts": recommendation_counts,
            "learning_summary": {
                "total_decision_count": len(items),
                "learning_candidate_count": len(observed),
                "unknown_count": len(unknown),
            },
            "synthesis_constraints": {
                "deterministic": True,
                "read_only": True,
                "source_backed_only": True,
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
