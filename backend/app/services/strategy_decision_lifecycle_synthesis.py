import sqlite3

from app.services.strategy_decision_lifecycle import StrategyDecisionLifecycleService


class StrategyDecisionLifecycleSynthesisService:
    """Synthesize lifecycle state without changing any underlying lifecycle data."""

    def __init__(self, lifecycle_service=None):
        self.lifecycle_service = lifecycle_service or StrategyDecisionLifecycleService()

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.lifecycle_service.get_context(conn, user_id, person_id)
        lifecycle = context["lifecycle"]
        ordered = sorted(
            lifecycle,
            key=lambda item: (item["decision"]["created_at"], item["decision_id"]),
        )

        result_counts = {
            "confirmed_pending_execution": 0,
            "executed_pending_outcome": 0,
            "outcome_recorded": 0,
            "not_actionable": 0,
        }
        feedback_counts = {
            "outcome_observed": 0,
            "outcome_unknown": 0,
        }

        for item in ordered:
            result_counts[item["result_status"]] += 1
            feedback_counts[item["feedback_status"]] += 1

        actionable = [
            item["decision_id"]
            for item in ordered
            if item["result_status"]
            in {"confirmed_pending_execution", "executed_pending_outcome"}
        ]
        feedback_learning = [
            item["decision_id"]
            for item in ordered
            if item["feedback_status"] == "outcome_observed"
        ]
        feedback_unknown = [
            item["decision_id"]
            for item in ordered
            if item["feedback_status"] == "outcome_unknown"
        ]

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "lifecycle": ordered,
            "actionable_decision_ids": actionable,
            "feedback_learning_decision_ids": feedback_learning,
            "feedback_unknown_decision_ids": feedback_unknown,
            "lifecycle_summary": {
                "total_decision_count": len(ordered),
                **{f"{key}_count": value for key, value in result_counts.items()},
                **{f"{key}_count": value for key, value in feedback_counts.items()},
            },
            "synthesis_constraints": {
                "deterministic": True,
                "read_only": True,
                "must_preserve_unknowns": True,
                "must_not_infer_recommendation_quality": True,
                "must_not_infer_relationship_impact": True,
                "must_not_auto_execute": True,
                "must_not_auto_send": True,
                "must_not_call_llm": True,
            },
        }
