import hashlib
import json


class StrategyRecommendationCandidateService:
    """Build explicit recommendation candidates at the Strategy -> Recommendation boundary."""

    @staticmethod
    def build_candidates(structured_analysis: dict) -> list[dict]:
        if not isinstance(structured_analysis, dict):
            return []

        hypotheses = structured_analysis.get("hypotheses") or []
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
            evidence_source_ids = list(dict.fromkeys(source_ids))
            identity_payload = {
                "recommendation": recommendation,
                "evidence_source_ids": evidence_source_ids,
            }
            candidate_id = "strategy-recommendation-" + hashlib.sha256(
                json.dumps(identity_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()[:24]
            candidates.append(
                {
                    "id": candidate_id,
                    "recommendation": recommendation,
                    "evidence_source_ids": evidence_source_ids,
                    "provenance": {
                        "source": "strategy_candidate",
                        "strategy_candidate_type": "analysis_hypothesis",
                        "source_evidence_ids": evidence_source_ids,
                        "unknowns_preserved": list(structured_analysis.get("unknowns") or []),
                    },
                }
            )

        return candidates
