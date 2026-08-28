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
            candidate
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
