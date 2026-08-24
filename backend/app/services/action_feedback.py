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
            },
            "feedback": self.repository.list_for_person(conn, user_id, person_id),
        }
