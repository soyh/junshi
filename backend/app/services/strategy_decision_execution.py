import sqlite3

from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_execution import ActionExecutionRepository
from app.repositories.action_outcome import ActionOutcomeRepository
from app.services.strategy_decision_confirmation import StrategyDecisionConfirmationService


class StrategyDecisionExecutionService:
    def __init__(
        self,
        confirmation_service=None,
        decision_repository=None,
        execution_repository=None,
        outcome_repository=None,
    ):
        self.confirmation_service = confirmation_service or StrategyDecisionConfirmationService()
        self.decision_repository = decision_repository or ActionDecisionRepository()
        self.execution_repository = execution_repository or ActionExecutionRepository()
        self.outcome_repository = outcome_repository or ActionOutcomeRepository()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.confirmation_service.get_context(conn, user_id, person_id)
        decisions = self.decision_repository.list_for_person(conn, user_id, person_id)
        executions = self.execution_repository.list_for_person(conn, user_id, person_id)
        outcomes = self.outcome_repository.list_for_person(conn, user_id, person_id)
        execution_by_decision = {item["decision_id"]: item for item in executions}
        outcome_decision_ids = {item["decision_id"] for item in outcomes}

        enriched = []
        for decision in decisions:
            execution = execution_by_decision.get(decision["id"])
            if decision["id"] in outcome_decision_ids:
                status = "outcome_recorded"
            elif execution is not None:
                status = "executed"
            elif decision["decision"] == "confirmed":
                status = "execution_ready"
            else:
                status = "not_executable"
            enriched.append({**decision, "execution_status": status})

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "decisions": enriched,
            "execution_constraints": {
                "must_require_confirmed_decision": True,
                "must_require_explicit_execution": True,
                "must_not_execute_rejected_decision": True,
                "must_not_execute_from_confirmation_automatically": True,
                "must_not_send": True,
                "must_not_create_outcome_automatically": True,
            },
        }

    def create_execution(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        decision_id: str,
        executed_at: str | None,
        note: str | None,
    ) -> dict:
        decision = self.decision_repository.get(conn, user_id, person_id, decision_id)
        if decision is None:
            raise ValueError("action decision not found")
        if decision["decision"] != "confirmed":
            raise ValueError("execution requires a confirmed action decision")
        if self.outcome_repository.get_by_decision(conn, user_id, person_id, decision_id) is not None:
            raise ValueError("execution is not available after an action outcome")
        if self.execution_repository.get_by_decision(conn, user_id, person_id, decision_id) is not None:
            raise ValueError("action decision has already been executed")
        return self.execution_repository.create(
            conn, user_id, person_id, decision_id, executed_at, note
        )
