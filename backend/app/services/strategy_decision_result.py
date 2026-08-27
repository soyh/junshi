import sqlite3

from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_execution import ActionExecutionRepository
from app.repositories.action_outcome import ActionOutcomeRepository
from app.services.strategy_decision_execution import StrategyDecisionExecutionService


class StrategyDecisionResultService:
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

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.execution_service.get_context(conn, user_id, person_id)
        decisions = self.decision_repository.list_for_person(conn, user_id, person_id)
        executions = self.execution_repository.list_for_person(conn, user_id, person_id)
        outcomes = self.outcome_repository.list_for_person(conn, user_id, person_id)
        execution_by_decision = {item["decision_id"]: item for item in executions}
        outcome_by_decision = {item["decision_id"]: item for item in outcomes}

        results = []
        for decision in decisions:
            decision_id = decision["id"]
            execution = execution_by_decision.get(decision_id)
            outcome = outcome_by_decision.get(decision_id)
            if outcome is not None:
                result_status = "outcome_recorded"
            elif execution is not None:
                result_status = "executed_pending_outcome"
            elif decision["decision"] == "confirmed":
                result_status = "confirmed_pending_execution"
            else:
                result_status = "not_actionable"
            results.append(
                {
                    **decision,
                    "result_status": result_status,
                    "execution": execution,
                    "outcome": outcome,
                }
            )

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "results": results,
            "result_constraints": {
                "execution_is_distinct_from_outcome": True,
                "must_not_execute_automatically": True,
                "must_not_create_outcome_automatically": True,
                "must_not_send": True,
            },
        }
