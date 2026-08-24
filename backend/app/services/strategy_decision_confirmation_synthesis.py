import sqlite3

from app.services.action_decision import ActionDecisionService
from app.services.strategy_decision_confirmation import StrategyDecisionConfirmationService


class StrategyDecisionConfirmationSynthesisService:
    def __init__(self, confirmation_service=None, action_decision_service=None):
        self.confirmation_service = confirmation_service or StrategyDecisionConfirmationService()
        self.action_decision_service = action_decision_service or ActionDecisionService()

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.confirmation_service.get_context(conn, user_id, person_id)
        decisions = self.action_decision_service.get_context(conn, user_id, person_id)["decisions"]
        confirmed = [item for item in decisions if item["decision"] == "confirmed"]
        rejected = [item for item in decisions if item["decision"] == "rejected"]
        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "confirmation_constraints": {
                **context["confirmation_constraints"],
                "must_not_execute_from_confirmation": True,
                "must_not_send_from_confirmation": True,
            },
            "confirmation_summary": {
                "decision_count": len(decisions),
                "confirmed_count": len(confirmed),
                "rejected_count": len(rejected),
                "latest_decision_id": decisions[0]["id"] if decisions else None,
            },
            "confirmed_recommendation_ids": [item["recommendation_id"] for item in confirmed],
            "rejected_recommendation_ids": [item["recommendation_id"] for item in rejected],
            "execution": {
                "ready": False,
                "requires_explicit_execution_step": True,
                "execution_is_automatic": False,
            },
        }
