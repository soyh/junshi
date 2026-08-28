import sqlite3

from app.services.action_plan import ActionPlanService
from app.services.learning_strategy_synthesis import LearningStrategySynthesisService


class ActionPlanLearningStrategyBridgeService:
    """Expose source-backed learning strategy synthesis alongside action-plan context."""

    def __init__(
        self,
        action_plan_service: ActionPlanService | None = None,
        learning_strategy_synthesis_service: LearningStrategySynthesisService | None = None,
    ):
        self.action_plan_service = action_plan_service or ActionPlanService()
        self.learning_strategy_synthesis_service = (
            learning_strategy_synthesis_service or LearningStrategySynthesisService()
        )

    @staticmethod
    def _project_candidate(candidate: dict) -> dict:
        return {
            "recommendation_id": candidate["recommendation_id"],
            "observed_outcome_count": candidate["observed_outcome_count"],
            "outcome_counts": candidate["outcome_counts"],
            "unknown_outcome_count": candidate["unknown_outcome_count"],
            "memory_update_count": candidate["memory_update_count"],
            "synthesis_status": candidate["synthesis_status"],
            "unknowns": list(candidate["unknowns"]),
            "source": dict(candidate["source"]),
        }

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        action_plan = self.action_plan_service.get_context(conn, user_id, person_id)
        synthesis = self.learning_strategy_synthesis_service.get_synthesis(
            conn, user_id, person_id
        )

        candidates = [
            self._project_candidate(candidate)
            for candidate in synthesis["candidates"]
            if candidate["observed_outcome_count"] > 0
        ]

        return {
            **action_plan,
            "learning_strategy": {
                "candidates": candidates,
                "strategy_decision_learning": synthesis["strategy_decision_learning"],
                "constraints": {
                    **synthesis["strategy_constraints"],
                    "must_not_auto_execute": True,
                },
            },
        }
