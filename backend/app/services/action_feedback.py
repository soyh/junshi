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

    def _load(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> tuple[dict, list[dict]]:
        context = self.action_plan_service.get_context(conn, user_id, person_id)
        feedback = self.repository.list_for_person(conn, user_id, person_id)
        return context, feedback

    @staticmethod
    def _synthesize(feedback: list[dict]) -> list[dict]:
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
                    "unknowns": ["action_effect", "relationship_impact"],
                    "source": {
                        "decision_id": item["decision_id"],
                        "outcome_id": item["outcome_id"],
                    },
                }
            )
        return synthesis

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context, feedback = self._load(conn, user_id, person_id)
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
            "feedback_synthesis": self._synthesize(feedback),
        }

    def get_summary(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context, feedback = self._load(conn, user_id, person_id)
        decision_counts = {"confirmed": 0, "rejected": 0}
        outcome_counts = {"completed": 0, "skipped": 0, "failed": 0}
        observed = 0
        unknown = 0
        latest_observed = None

        for item in feedback:
            decision = item["decision"]
            if decision in decision_counts:
                decision_counts[decision] += 1
            if item.get("outcome_id") and item.get("outcome"):
                observed += 1
                outcome = item["outcome"]
                if outcome in outcome_counts:
                    outcome_counts[outcome] += 1
                if latest_observed is None:
                    latest_observed = {
                        "decision_id": item["decision_id"],
                        "outcome_id": item["outcome_id"],
                        "outcome": outcome,
                        "created_at": item["outcome_created_at"],
                    }
            else:
                unknown += 1

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "feedback_summary_constraints": {
                "must_be_source_backed": True,
                "must_preserve_unknowns": True,
                "must_not_infer_relationship_impact": True,
                "must_not_infer_success_from_missing_outcome": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
            },
            "summary": {
                "total_decisions": len(feedback),
                "decision_counts": decision_counts,
                "outcome_observed_count": observed,
                "outcome_unknown_count": unknown,
                "outcome_counts": outcome_counts,
                "latest_observed_outcome": latest_observed,
            },
        }

    def get_trend(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context, feedback = self._load(conn, user_id, person_id)
        observations = []
        for item in feedback:
            observed = bool(item.get("outcome_id") and item.get("outcome"))
            observations.append(
                {
                    "event_at": item["outcome_created_at"] if observed else item["decision_created_at"],
                    "feedback_status": "outcome_observed" if observed else "outcome_unknown",
                    "decision_id": item["decision_id"],
                    "decision": item["decision"],
                    "decision_created_at": item["decision_created_at"],
                    "outcome_id": item["outcome_id"],
                    "outcome": item["outcome"] if observed else "unknown",
                    "outcome_created_at": item["outcome_created_at"],
                    "source": {
                        "decision_id": item["decision_id"],
                        "outcome_id": item["outcome_id"],
                    },
                }
            )

        observations.sort(key=lambda item: (item["event_at"], item["decision_id"]), reverse=True)
        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "feedback_trend_constraints": {
                "must_be_source_backed": True,
                "must_preserve_unknowns": True,
                "must_have_deterministic_ordering": True,
                "must_not_infer_relationship_impact": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
            },
            "observations": observations,
        }
