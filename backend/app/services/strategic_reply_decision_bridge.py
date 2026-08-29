import sqlite3

from app.services.strategy_decision_result import StrategyDecisionResultService
from app.services.strategic_reply import StrategicReplyService


class StrategicReplyDecisionBridgeService:
    """Expose explicit strategy decisions as a read-only Strategic Reply downstream boundary."""

    def __init__(
        self,
        strategic_reply_service: StrategicReplyService | None = None,
        decision_result_service: StrategyDecisionResultService | None = None,
    ):
        self.strategic_reply_service = strategic_reply_service or StrategicReplyService()
        self.decision_result_service = decision_result_service or StrategyDecisionResultService()

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        reply_context = self.strategic_reply_service.get_context(conn, user_id, person_id)
        result_context = self.decision_result_service.get_context(conn, user_id, person_id)

        confirmed = [
            {
                "decision_id": item["id"],
                "recommendation_id": item["recommendation_id"],
                "decision": item["decision"],
                "result_status": item["result_status"],
                "created_at": item["created_at"],
            }
            for item in result_context["results"]
            if item["decision"] == "confirmed"
        ]

        return {
            **reply_context,
            "decision_downstream": {
                "confirmed_decisions": confirmed,
                "selection_status": "explicitly_confirmed" if confirmed else "requires_explicit_decision",
                "selection_is_automatic": False,
            },
            "reply_constraints": {
                **dict(reply_context.get("reply_constraints") or {}),
                "must_require_explicit_decision": True,
                "must_not_auto_select": True,
                "must_not_auto_confirm": True,
                "must_not_auto_send": True,
                "must_not_auto_execute": True,
            },
        }
