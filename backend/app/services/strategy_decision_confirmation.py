import sqlite3

from app.repositories.action_decision import ActionDecisionRepository
from app.services.strategy_decision_synthesis import StrategyDecisionSynthesisService


class StrategyDecisionConfirmationService:
    def __init__(self, synthesis_service=None, repository=None):
        self.synthesis_service = synthesis_service or StrategyDecisionSynthesisService()
        self.repository = repository or ActionDecisionRepository()

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
        candidates = {item["recommendation_id"]: item for item in context["decisions"]}
        if recommendation_id is not None and recommendation_id not in candidates:
            raise ValueError("recommendation is not available for explicit decision")
        if decision == "confirmed" and recommendation_id is None:
            raise ValueError("confirmed decision requires recommendation_id")
        if decision == "confirmed" and candidates[recommendation_id]["decision_status"] != "decisionable":
            raise ValueError("recommendation is not decisionable")
        return self.repository.create(
            conn, user_id, person_id, recommendation_id, decision, note
        )
