import sqlite3

from app.services.recommendation import RecommendationService


class StrategicReplyService:
    def __init__(self, recommendation_service: RecommendationService | None = None):
        self.recommendation_service = recommendation_service or RecommendationService()

    @staticmethod
    def build_draft(recommendations: list, evidence: list[dict]) -> str | None:
        """Select the first explicit, evidence-backed reply draft without inventing text."""
        evidence_ids = {
            item.get("source_id")
            for item in evidence
            if isinstance(item, dict) and item.get("source_id")
        }

        for recommendation in recommendations:
            if not isinstance(recommendation, dict):
                continue

            reply = recommendation.get("reply")
            source_ids = recommendation.get("evidence_source_ids")
            if not isinstance(reply, str) or not reply.strip():
                continue
            if not isinstance(source_ids, list) or not source_ids:
                continue
            if not all(
                isinstance(source_id, str) and source_id in evidence_ids
                for source_id in source_ids
            ):
                continue

            return reply.strip()

        return None

    def build_context_from_recommendation_context(
        self,
        context: dict,
        *,
        reply_candidates: list[dict] | None = None,
        derived: bool = False,
    ) -> dict:
        recommendations = context.get("recommendations")
        evidence = context.get("evidence")
        if not isinstance(recommendations, list):
            recommendations = []
        if not isinstance(evidence, list):
            evidence = []

        candidates = recommendations if reply_candidates is None else reply_candidates
        reply_constraints = {
            "must_be_evidence_backed": True,
            "must_preserve_unknowns": True,
            "must_not_auto_send": True,
            "must_not_change_relationship": True,
        }
        if derived:
            reply_constraints.update(
                {
                    "must_preserve_evidence_provenance": True,
                    "must_treat_llm_output_as_derived": True,
                }
            )

        return {
            **context,
            "reply_constraints": reply_constraints,
            "draft": self.build_draft(candidates, evidence),
        }

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        context = self.recommendation_service.get_context(conn, user_id, person_id)
        return self.build_context_from_recommendation_context(context)
