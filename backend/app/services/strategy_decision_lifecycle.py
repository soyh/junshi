import sqlite3

from app.repositories.action_feedback import ActionFeedbackRepository
from app.services.action_feedback import ActionFeedbackService
from app.services.strategy_decision_result import StrategyDecisionResultService


class StrategyDecisionLifecycleService:
    """Build a read-only, deterministic decision lifecycle context."""

    def __init__(
        self,
        result_service=None,
        feedback_service=None,
        feedback_repository=None,
    ):
        self.result_service = result_service or StrategyDecisionResultService()
        self.feedback_service = feedback_service or ActionFeedbackService()
        self.feedback_repository = feedback_repository or ActionFeedbackRepository()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        result_context = self.result_service.get_context(conn, user_id, person_id)
        feedback_context = self.feedback_service.get_context(conn, user_id, person_id)
        feedback_by_decision = {
            item["decision_id"]: item
            for item in feedback_context["feedback_synthesis"]
        }

        lifecycle = []
        for result in result_context["results"]:
            decision_id = result["id"]
            feedback = feedback_by_decision.get(decision_id)
            lifecycle.append(
                {
                    "decision_id": decision_id,
                    "decision": result,
                    "result_status": result["result_status"],
                    "feedback_status": feedback["feedback_status"] if feedback else "outcome_unknown",
                    "execution_present": result["execution"] is not None,
                    "outcome_present": result["outcome"] is not None,
                    "feedback": feedback,
                    "source": {
                        "decision_id": decision_id,
                        "outcome_id": result["outcome"]["id"] if result["outcome"] else None,
                    },
                }
            )

        lifecycle.sort(key=lambda item: (item["decision"]["created_at"], item["decision_id"]))

        return {
            "person": result_context["person"],
            "relationship": result_context["relationship"],
            "lifecycle": lifecycle,
            "lifecycle_constraints": {
                "read_only": True,
                "execution_is_distinct_from_outcome": True,
                "outcome_is_not_automatic_execution": True,
                "feedback_must_be_source_backed": True,
                "feedback_unknowns_must_be_preserved": True,
                "relationship_impact_must_not_be_inferred": True,
                "must_not_auto_execute": True,
                "must_not_auto_send": True,
                "must_not_call_llm": True,
            },
        }
