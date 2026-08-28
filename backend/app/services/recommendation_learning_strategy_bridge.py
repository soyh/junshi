import sqlite3

from app.services.learning_strategy_synthesis import LearningStrategySynthesisService
from app.services.recommendation import RecommendationService


class RecommendationLearningStrategyBridgeService:
    """Expose source-backed learning strategy synthesis alongside recommendation context."""

    def __init__(
        self,
        recommendation_service: RecommendationService | None = None,
        learning_strategy_synthesis_service: LearningStrategySynthesisService | None = None,
    ):
        self.recommendation_service = recommendation_service or RecommendationService()
        self.learning_strategy_synthesis_service = (
            learning_strategy_synthesis_service or LearningStrategySynthesisService()
        )

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        recommendation = self.recommendation_service.get_context(conn, user_id, person_id)
        synthesis = self.learning_strategy_synthesis_service.get_synthesis(
            conn, user_id, person_id
        )

        candidates = [
            candidate
            for candidate in synthesis["candidates"]
            if candidate["observed_outcome_count"] > 0
        ]

        return {
            **recommendation,
            "learning_strategy": {
                "candidates": candidates,
                "strategy_decision_learning": synthesis["strategy_decision_learning"],
                "constraints": synthesis["strategy_constraints"],
            },
        }
