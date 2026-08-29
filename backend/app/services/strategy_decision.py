import sqlite3

from app.schemas.structured_analysis import StructuredAnalysis
from app.services.learning_strategy_synthesis import LearningStrategySynthesisService
from app.services.strategy_analysis_bridge import StrategyAnalysisBridgeService


class StrategyDecisionContextService:
    def __init__(
        self,
        synthesis_service: LearningStrategySynthesisService | None = None,
        analysis_bridge_service: StrategyAnalysisBridgeService | None = None,
    ):
        self.synthesis_service = synthesis_service or LearningStrategySynthesisService()
        self.analysis_bridge_service = analysis_bridge_service or StrategyAnalysisBridgeService()

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        *,
        structured_analysis: StructuredAnalysis | None = None,
    ) -> dict:
        synthesis = self.synthesis_service.get_synthesis(conn, user_id, person_id)
        candidates = synthesis["candidates"]
        context = {
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

        if structured_analysis is not None:
            context = self.analysis_bridge_service.build_input(context, structured_analysis)

        return context

    @staticmethod
    def _current_state(relationship: dict) -> dict:
        return {
            "status": relationship.get("status"),
            "stage": relationship.get("stage"),
        }
