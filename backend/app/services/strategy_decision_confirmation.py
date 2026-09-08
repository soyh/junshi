import sqlite3

from app.services.strategy_decision_synthesis import StrategyDecisionSynthesisService


class StrategyDecisionConfirmationService:
    def __init__(self, synthesis_service=None):
        self.synthesis_service = synthesis_service or StrategyDecisionSynthesisService()

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
