import sqlite3

from app.repositories.action_plan_snapshot import ActionPlanSnapshotRepository
from app.services.strategic_reply import StrategicReplyService


class ActionPlanService:
    def __init__(
        self,
        strategic_reply_service: StrategicReplyService | None = None,
        snapshot_repository: ActionPlanSnapshotRepository | None = None,
    ):
        self.strategic_reply_service = strategic_reply_service or StrategicReplyService()
        self.snapshot_repository = snapshot_repository or ActionPlanSnapshotRepository()

    @staticmethod
    def build_action_plan(recommendations: list, evidence: list[dict]) -> list[dict]:
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
            if not all(isinstance(source_id, str) and source_id in evidence_ids for source_id in source_ids):
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

    def persist_action_plan(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        recommendations: list[dict],
        action_plan: list[dict],
        evidence: list[dict],
    ) -> None:
        plans_by_id = {
            item.get("recommendation_id"): item
            for item in action_plan
            if item.get("recommendation_id")
        }
        for recommendation in recommendations:
            recommendation_id = recommendation.get("id")
            if recommendation_id in plans_by_id:
                self.snapshot_repository.upsert(
                    conn,
                    user_id,
                    person_id,
                    recommendation,
                    plans_by_id[recommendation_id],
                    evidence,
                )

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.strategic_reply_service.get_context(conn, user_id, person_id)
        if conn is None:
            recommendations = list(context.get("recommendations", []))
            action_plan = self.build_action_plan(recommendations, context["evidence"])
        else:
            current_evidence_ids = {
                item.get("source_id")
                for item in context.get("evidence", [])
                if isinstance(item, dict) and item.get("source_id")
            }
            snapshots = []
            for item in self.snapshot_repository.list_for_person(conn, user_id, person_id):
                recommendation = item["recommendation"]
                action_plan_item = item["action_plan"]
                recommendation_evidence = recommendation.get("evidence_source_ids")
                action_plan_evidence = action_plan_item.get("evidence_source_ids")
                if not isinstance(recommendation_evidence, list) or not recommendation_evidence:
                    continue
                if not isinstance(action_plan_evidence, list) or not action_plan_evidence:
                    continue
                if not all(source_id in current_evidence_ids for source_id in recommendation_evidence):
                    continue
                if not all(source_id in current_evidence_ids for source_id in action_plan_evidence):
                    continue
                snapshots.append(item)
            recommendations = [item["recommendation"] for item in snapshots]
            action_plan = [item["action_plan"] for item in snapshots]
        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "current_state": context["current_state"],
            "evidence": context["evidence"],
            "facts": context["facts"],
            "inferences": context["inferences"],
            "unknowns": context["unknowns"],
            "recommendations": recommendations,
            "action_plan": action_plan,
            "action_constraints": {
                "must_be_evidence_backed": True,
                "must_preserve_unknowns": True,
                "requires_user_confirmation": True,
                "must_not_auto_execute": True,
                "must_not_change_relationship": True,
            },
        }
