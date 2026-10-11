import sqlite3

from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_execution import ActionExecutionRepository
from app.repositories.action_outcome import ActionOutcomeRepository
from app.services.strategy_decision_execution import StrategyDecisionExecutionService


class StrategyDecisionExecutionSynthesisService:
    def __init__(
        self,
        execution_service=None,
        decision_repository=None,
        execution_repository=None,
        outcome_repository=None,
    ):
        self.execution_service = execution_service or StrategyDecisionExecutionService()
        self.decision_repository = decision_repository or ActionDecisionRepository()
        self.execution_repository = execution_repository or ActionExecutionRepository()
        self.outcome_repository = outcome_repository or ActionOutcomeRepository()

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.execution_service.get_context(conn, user_id, person_id)
        decisions = self.decision_repository.list_for_person(conn, user_id, person_id)
        executions = self.execution_repository.list_for_person(conn, user_id, person_id)
        outcomes = self.outcome_repository.list_for_person(conn, user_id, person_id)
        execution_ids = {item["decision_id"] for item in executions}
        outcome_ids = {item["decision_id"] for item in outcomes}
        confirmed = [item for item in decisions if item["decision"] == "confirmed"]
        pending = [
            item["id"]
            for item in confirmed
            if item["id"] not in execution_ids and item["id"] not in outcome_ids
        ]
        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "executions": executions,
            "pending_decision_ids": pending,
            "execution_summary": {
                "confirmed_count": len(confirmed),
                "executed_count": len(executions),
                "outcome_recorded_count": len(outcome_ids),
                "pending_execution_count": len(pending),
                "latest_execution_id": executions[0]["id"] if executions else None,
            },
        }
