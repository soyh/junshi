import sqlite3

from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_outcome import ActionOutcomeRepository
from app.services.strategy_decision_confirmation import StrategyDecisionConfirmationService


class StrategyDecisionConfirmationSynthesisService:
    def __init__(self, confirmation_service=None, decision_repository=None, outcome_repository=None):
        self.confirmation_service = confirmation_service or StrategyDecisionConfirmationService()
        self.decision_repository = decision_repository or ActionDecisionRepository()
        self.outcome_repository = outcome_repository or ActionOutcomeRepository()

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.confirmation_service.get_context(conn, user_id, person_id)
        decisions = self.decision_repository.list_for_person(conn, user_id, person_id)
        outcomes = self.outcome_repository.list_for_person(conn, user_id, person_id)
        outcome_decision_ids = {item["decision_id"] for item in outcomes}
        confirmations = [item for item in decisions if item["id"] not in outcome_decision_ids]
        confirmed = [item for item in confirmations if item["decision"] == "confirmed"]
        rejected = [item for item in confirmations if item["decision"] == "rejected"]
        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "confirmation_constraints": {
                **context["confirmation_constraints"],
                "must_not_execute_from_confirmation": True,
                "must_not_send_from_confirmation": True,
            },
            "confirmation_summary": {
                "decision_count": len(confirmations),
                "confirmed_count": len(confirmed),
                "rejected_count": len(rejected),
                "latest_decision_id": confirmations[0]["id"] if confirmations else None,
            },
            "confirmed_recommendation_ids": [item["recommendation_id"] for item in confirmed],
            "rejected_recommendation_ids": [item["recommendation_id"] for item in rejected],
            "execution": {
                "ready": False,
                "requires_explicit_execution_step": True,
                "execution_is_automatic": False,
            },
        }
