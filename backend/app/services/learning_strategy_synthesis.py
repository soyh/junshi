import sqlite3

from app.services.learning_strategy_context import LearningStrategyContextService


class LearningStrategySynthesisService:
    def __init__(self, context_service: LearningStrategyContextService | None = None):
        self.context_service = context_service or LearningStrategyContextService()

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.context_service.get_context(conn, user_id, person_id)
        grouped = {}
        for item in context["learning_inputs"]["action_feedback"]:
            recommendation_id = item["recommendation_id"]
            grouped[recommendation_id] = {
                "recommendation_id": recommendation_id,
                "observed_outcome_count": item["observed_outcome_count"],
                "outcome_counts": item["outcome_counts"],
                "unknown_outcome_count": item["unknown_outcome_count"],
                "memory_update_count": 0,
                "synthesis_status": "source_backed_candidate"
                if item["observed_outcome_count"] > 0
                else "outcome_unknown",
                "unknowns": [
                    "recommendation_quality",
                    "success",
                    "relationship_impact",
                ],
            }

        for update in context["learning_inputs"]["memory_updates"]:
            recommendation_id = update["learning_provenance"].get("recommendation_id")
            if recommendation_id in grouped:
                grouped[recommendation_id]["memory_update_count"] += 1

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "strategy_constraints": {
                **context["strategy_constraints"],
                "must_not_turn_learning_into_fact": True,
                "must_not_rank_recommendations": True,
            },
            "candidates": list(grouped.values()),
        }
