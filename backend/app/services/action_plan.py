import sqlite3

from app.services.strategic_reply import StrategicReplyService


class ActionPlanService:
    def __init__(self, strategic_reply_service: StrategicReplyService | None = None):
        self.strategic_reply_service = strategic_reply_service or StrategicReplyService()

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        context = self.strategic_reply_service.get_context(conn, user_id, person_id)
        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "current_state": context["current_state"],
            "evidence": context["evidence"],
            "facts": context["facts"],
            "inferences": context["inferences"],
            "unknowns": context["unknowns"],
            "recommendations": context["recommendations"],
            "action_plan": [],
            "action_constraints": {
                "must_be_evidence_backed": True,
                "must_preserve_unknowns": True,
                "requires_user_confirmation": True,
                "must_not_auto_execute": True,
                "must_not_change_relationship": True,
            },
        }
