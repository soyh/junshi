import sqlite3

from app.services.learning_strategy_synthesis import LearningStrategySynthesisService
from app.services.strategic_reply import StrategicReplyService


class StrategicReplyLearningStrategyBridgeService:
    """Expose source-backed learning strategy synthesis alongside strategic reply context."""

    def __init__(
        self,
        strategic_reply_service: StrategicReplyService | None = None,
        learning_strategy_synthesis_service: LearningStrategySynthesisService | None = None,
    ):
        self.strategic_reply_service = strategic_reply_service or StrategicReplyService()
        self.learning_strategy_synthesis_service = (
            learning_strategy_synthesis_service or LearningStrategySynthesisService()
        )

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        reply = self.strategic_reply_service.get_context(conn, user_id, person_id)
        synthesis = self.learning_strategy_synthesis_service.get_synthesis(
            conn, user_id, person_id
        )

        candidates = [
            candidate
            for candidate in synthesis["candidates"]
            if candidate["observed_outcome_count"] > 0
        ]

        return {
            **reply,
            "learning_strategy": {
                "candidates": candidates,
                "strategy_decision_learning": synthesis["strategy_decision_learning"],
                "constraints": {
                    **synthesis["strategy_constraints"],
                    "must_not_auto_send": True,
                },
            },
        }
