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

        strategy_decision = context["learning_inputs"]["strategy_decision"]
        strategy_decision_observed = [
            item for item in strategy_decision["items"] if item["learning_eligible"]
        ]
        strategy_decision_unknown = [
            item for item in strategy_decision["items"] if not item["learning_eligible"]
        ]
        strategy_decision_counts = {}
        for item in strategy_decision_observed:
            recommendation_id = item["recommendation_id"]
            strategy_decision_counts[recommendation_id] = (
                strategy_decision_counts.get(recommendation_id, 0) + 1
            )

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "strategy_constraints": {
                **context["strategy_constraints"],
                "must_not_turn_learning_into_fact": True,
                "must_not_rank_recommendations": True,
            },
            "candidates": list(grouped.values()),
            "strategy_decision_learning": {
                "learning_candidate_decision_ids": [
                    item["decision_id"] for item in strategy_decision_observed
                ],
                "unknown_decision_ids": [item["decision_id"] for item in strategy_decision_unknown],
                "recommendation_observed_counts": strategy_decision_counts,
                "learning_candidate_count": len(strategy_decision_observed),
                "unknown_count": len(strategy_decision_unknown),
                "constraints": {
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
            },
        }
