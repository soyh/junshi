import hashlib
import sqlite3

from app.services.strategy_decision import StrategyDecisionContextService


class StrategyRecommendationCandidateService:
    """Build explicit recommendation candidates at the Strategy -> Recommendation boundary."""

    def __init__(self, strategy_decision_service: StrategyDecisionContextService | None = None):
        self.strategy_decision_service = strategy_decision_service or StrategyDecisionContextService()

    def build_candidates(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        *,
        structured_analysis: dict | None = None,
    ) -> list[dict]:
        context = self.strategy_decision_service.get_context(
            conn,
            user_id,
            person_id,
        )
        analysis = structured_analysis or context.get("structured_analysis") or {}
        hypotheses = analysis.get("hypotheses") or []

        candidates: list[dict] = []
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                continue
            content = hypothesis.get("content")
            source_ids = hypothesis.get("evidence_source_ids")
            if not isinstance(content, str) or not content.strip():
                continue
            if not isinstance(source_ids, list) or not source_ids:
                continue
            if not all(isinstance(source_id, str) and source_id.strip() for source_id in source_ids):
                continue

            recommendation = content.strip()
            candidate_id = "strategy-recommendation-" + hashlib.sha256(
                recommendation.encode("utf-8")
            ).hexdigest()[:24]
            candidates.append(
                {
                    "id": candidate_id,
                    "recommendation": recommendation,
                    "evidence_source_ids": list(dict.fromkeys(source_ids)),
                    "provenance": {
                        "source": "strategy_candidate",
                        "strategy_candidate_type": "analysis_hypothesis",
                        "source_evidence_ids": list(dict.fromkeys(source_ids)),
                        "unknowns_preserved": list(analysis.get("unknowns") or []),
                    },
                }
            )

        return candidates
