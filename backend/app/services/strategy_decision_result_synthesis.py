import sqlite3

from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_execution import ActionExecutionRepository
from app.repositories.action_outcome import ActionOutcomeRepository
from app.services.strategy_decision_result import StrategyDecisionResultService


class StrategyDecisionResultSynthesisService:
    def __init__(
        self,
        result_service=None,
        decision_repository=None,
        execution_repository=None,
        outcome_repository=None,
    ):
        self.result_service = result_service or StrategyDecisionResultService()
        self.decision_repository = decision_repository or ActionDecisionRepository()
        self.execution_repository = execution_repository or ActionExecutionRepository()
        self.outcome_repository = outcome_repository or ActionOutcomeRepository()

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.result_service.get_context(conn, user_id, person_id)
        results = context["results"]
        status_counts = {
            "outcome_recorded": 0,
            "executed_pending_outcome": 0,
            "confirmed_pending_execution": 0,
            "not_actionable": 0,
        }
        for item in results:
            status_counts[item["result_status"]] += 1

        actionable = [
            item["id"]
            for item in results
            if item["result_status"] in {
                "confirmed_pending_execution",
                "executed_pending_outcome",
            }
        ]
        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "results": results,
            "actionable_decision_ids": actionable,
            "result_summary": {
                "total_decision_count": len(results),
                **{f"{key}_count": value for key, value in status_counts.items()},
            },
        }
