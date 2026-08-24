import sqlite3

from app.repositories.action_feedback import ActionFeedbackRepository
from app.services.action_plan import ActionPlanService


class ActionFeedbackService:
    def __init__(
        self,
        action_plan_service: ActionPlanService | None = None,
        repository: ActionFeedbackRepository | None = None,
    ):
        self.action_plan_service = action_plan_service or ActionPlanService()
        self.repository = repository or ActionFeedbackRepository()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.action_plan_service.get_context(conn, user_id, person_id)
        feedback = self.repository.list_for_person(conn, user_id, person_id)
        synthesis = []

        for item in feedback:
            outcome_observed = bool(item.get("outcome_id") and item.get("outcome"))
            synthesis.append(
                {
                    "decision_id": item["decision_id"],
                    "outcome_id": item["outcome_id"],
                    "feedback_status": "outcome_observed" if outcome_observed else "outcome_unknown",
                    "decision_signal": item["decision"],
                    "outcome_signal": item["outcome"] if outcome_observed else "unknown",
                    "unknowns": [
                        "action_effect",
                        "relationship_impact",
                    ],
                    "source": {
                        "decision_id": item["decision_id"],
                        "outcome_id": item["outcome_id"],
                    },
                }
            )

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "feedback_constraints": {
                "must_be_decision_backed": True,
                "must_be_outcome_backed": False,
                "must_preserve_unknowns": True,
                "must_not_infer_success_from_missing_outcome": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
                "must_have_explicit_feedback_status": True,
            },
            "feedback": feedback,
            "feedback_synthesis": synthesis,
        }
