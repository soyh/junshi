import sqlite3

from app.services.strategic_reply import StrategicReplyService


class ActionPlanService:
    def __init__(self, strategic_reply_service: StrategicReplyService | None = None):
        self.strategic_reply_service = strategic_reply_service or StrategicReplyService()

    @staticmethod
    def build_action_plan(
        recommendations: list,
        evidence: list[dict],
    ) -> list[dict]:
        """Promote only explicit, evidence-backed recommendations to proposals."""
        evidence_ids = {
            item.get("source_id")
            for item in evidence
            if isinstance(item, dict) and item.get("source_id")
        }
        action_plan: list[dict] = []

        for recommendation in recommendations:
            if not isinstance(recommendation, dict):
                continue

            action = recommendation.get("action")
            source_ids = recommendation.get("evidence_source_ids")
            if not isinstance(action, str) or not action.strip():
                continue
            if not isinstance(source_ids, list) or not source_ids:
                continue
            if not all(
                isinstance(source_id, str) and source_id in evidence_ids
                for source_id in source_ids
            ):
                continue

            item = {
                "recommendation_id": recommendation.get("id"),
                "action": action,
                "evidence_source_ids": list(source_ids),
                "status": "proposed",
                "requires_user_confirmation": True,
            }
            if recommendation.get("priority") is not None:
                item["priority"] = recommendation["priority"]
            if recommendation.get("time_horizon") is not None:
                item["time_horizon"] = recommendation["time_horizon"]
            action_plan.append(item)

        return action_plan

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
            "action_plan": self.build_action_plan(
                context["recommendations"],
                context["evidence"],
            ),
            "action_constraints": {
                "must_be_evidence_backed": True,
                "must_preserve_unknowns": True,
                "requires_user_confirmation": True,
                "must_not_auto_execute": True,
                "must_not_change_relationship": True,
            },
        }
