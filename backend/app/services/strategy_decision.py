import sqlite3

from app.services.learning_strategy_synthesis import LearningStrategySynthesisService


class StrategyDecisionContextService:
    def __init__(self, synthesis_service: LearningStrategySynthesisService | None = None):
        self.synthesis_service = synthesis_service or LearningStrategySynthesisService()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        synthesis = self.synthesis_service.get_synthesis(conn, user_id, person_id)
        candidates = synthesis["candidates"]
        return {
            "person": synthesis["person"],
            "relationship": synthesis["relationship"],
            "current_state": self._current_state(synthesis["relationship"]),
            "strategy_constraints": {
                **synthesis["strategy_constraints"],
                "must_not_auto_select": True,
            },
            "candidates": candidates,
            "decision_inputs": {
                "candidate_count": len(candidates),
                "candidate_ids": [item["recommendation_id"] for item in candidates],
                "selection_status": "requires_explicit_decision",
                "observed_outcome_counts": {
                    item["recommendation_id"]: item["observed_outcome_count"]
                    for item in candidates
                },
                "unknown_outcome_counts": {
                    item["recommendation_id"]: item["unknown_outcome_count"]
                    for item in candidates
                },
            },
        }

    @staticmethod
    def _current_state(relationship: dict) -> dict:
        return {
            "status": relationship.get("status"),
            "stage": relationship.get("stage"),
        }
