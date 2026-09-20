from typing import Any

from app.schemas.strategic_reply_generation import StrategicReplyGeneration
from app.services.llm import LLMAnalysisError, LLMProvider


class StrategicReplyLLMService:
    """Generate one derived reply draft from evidence-backed recommendations."""

    def generate(
        self,
        context: dict[str, Any],
        *,
        provider: LLMProvider,
    ) -> dict[str, Any] | None:
        recommendations = context.get("recommendations")
        evidence = context.get("evidence")
        if not isinstance(recommendations, list) or not recommendations:
            return None
        if not isinstance(evidence, list) or not evidence:
            return None

        try:
            result = provider.generate_strategic_reply(context)
        except LLMAnalysisError:
            raise
        except Exception:
            raise LLMAnalysisError("LLM strategic reply provider failed") from None

        if not isinstance(result, dict):
            raise LLMAnalysisError("LLM provider returned a non-object strategic reply")

        try:
            candidate = StrategicReplyGeneration.model_validate(result)
        except Exception:
            raise LLMAnalysisError("LLM provider returned invalid strategic reply") from None

        recommendation_by_id = {
            item.get("id"): item
            for item in recommendations
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        selected = []
        for recommendation_id in candidate.recommendation_ids:
            item = recommendation_by_id.get(recommendation_id)
            if item is None:
                raise LLMAnalysisError(
                    "LLM provider returned invalid strategic reply provenance"
                )
            selected.append(item)

        canonical_evidence_ids = {
            item.get("source_id")
            for item in evidence
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }
        allowed_evidence_ids = {
            source_id
            for item in selected
            for source_id in item.get("evidence_source_ids", [])
            if isinstance(source_id, str)
        }

        if not all(
            source_id in canonical_evidence_ids and source_id in allowed_evidence_ids
            for source_id in candidate.evidence_source_ids
        ):
            raise LLMAnalysisError(
                "LLM provider returned invalid strategic reply provenance"
            )

        return candidate.model_dump(mode="json")
