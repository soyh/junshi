import sqlite3

from app.services.strategy_decision import StrategyDecisionContextService


class StrategyDecisionSynthesisService:
    def __init__(self, context_service: StrategyDecisionContextService | None = None):
        self.context_service = context_service or StrategyDecisionContextService()

    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        context = self.context_service.get_context(conn, user_id, person_id)
        decisions = []
        for candidate in context["candidates"]:
            observed = candidate["observed_outcome_count"]
            unknown = candidate["unknown_outcome_count"]
            decisions.append(
                {
                    "recommendation_id": candidate["recommendation_id"],
                    "decision_status": "decisionable" if observed > 0 else "insufficient_evidence",
                    "observed_outcome_count": observed,
                    "unknown_outcome_count": unknown,
                    "decision_reasons": [
                        "observed_outcome_available" if observed > 0 else "observed_outcome_missing",
                        "unknown_outcomes_preserved" if unknown > 0 else "no_unknown_outcomes",
                    ],
                    "unknowns": [
                        "recommendation_quality",
                        "success",
                        "relationship_impact",
                    ],
                }
            )

        return {
            "person": context["person"],
            "relationship": context["relationship"],
            "strategy_constraints": {
                **context["strategy_constraints"],
                "must_not_auto_select": True,
                "must_not_rank_recommendations": True,
                "must_not_turn_decision_status_into_fact": True,
            },
            "decisions": decisions,
            "selection": {
                "selected_recommendation_id": None,
                "selection_status": "requires_explicit_decision",
                "selection_is_automatic": False,
            },
        }
