import sqlite3

from app.repositories.action_decision import ActionDecisionRepository
from app.services.action_plan import ActionPlanService


class ActionDecisionService:
    def __init__(
        self,
        action_plan_service: ActionPlanService | None = None,
        repository: ActionDecisionRepository | None = None,
    ):
        self.action_plan_service = action_plan_service or ActionPlanService()
        self.repository = repository or ActionDecisionRepository()

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.action_plan_service.get_context(conn, user_id, person_id)
        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "action_plan": context["action_plan"],
            "action_constraints": {
                **context["action_constraints"],
                "must_record_user_decision": True,
                "must_not_auto_execute": True,
            },
            "decisions": self.repository.list_for_person(conn, user_id, person_id),
        }

    def create_decision(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        recommendation_id: str | None,
        decision: str,
        note: str | None,
    ) -> dict:
        context = self.action_plan_service.get_context(conn, user_id, person_id)
        if recommendation_id is not None:
            allowed_ids = {
                item.get("recommendation_id")
                for item in context["action_plan"]
                if item.get("recommendation_id")
            }
            if recommendation_id not in allowed_ids:
                raise ValueError("recommendation is not an available evidence-backed action")

        if decision == "confirmed" and recommendation_id is None:
            raise ValueError("confirmed decision requires recommendation_id")

        return self.repository.create(
            conn,
            user_id,
            person_id,
            recommendation_id,
            decision,
            note,
        )
