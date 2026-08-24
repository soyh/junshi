import sqlite3

from app.services.action_decision import ActionDecisionService
from app.services.strategy_decision_synthesis import StrategyDecisionSynthesisService


class StrategyDecisionConfirmationService:
    def __init__(self, synthesis_service=None, action_decision_service=None):
        self.synthesis_service = synthesis_service or StrategyDecisionSynthesisService()
        self.action_decision_service = action_decision_service or ActionDecisionService()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        synthesis = self.synthesis_service.get_synthesis(conn, user_id, person_id)
        return {
            "person": synthesis["person"],
            "relationship": synthesis["relationship"],
            "decisions": synthesis["decisions"],
            "confirmation_constraints": {
                "must_record_user_decision": True,
                "must_not_auto_confirm": True,
                "must_not_auto_execute": True,
                "must_not_auto_send": True,
            },
        }

    def create_confirmation(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        recommendation_id: str | None,
        decision: str,
        note: str | None,
    ) -> dict:
        context = self.synthesis_service.get_synthesis(conn, user_id, person_id)
        allowed_ids = {item["recommendation_id"] for item in context["decisions"]}
        if recommendation_id is not None and recommendation_id not in allowed_ids:
            raise ValueError("recommendation is not available for explicit decision")
        if decision == "confirmed" and recommendation_id is None:
            raise ValueError("confirmed decision requires recommendation_id")
        return self.action_decision_service.create_decision(
            conn, user_id, person_id, recommendation_id, decision, note
        )
