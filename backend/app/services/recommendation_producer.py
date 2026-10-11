from app.schemas.recommendation import Recommendation


class RecommendationProducer:
    """Produce typed recommendations from explicit strategy candidates only.

    This boundary deliberately does not accept StructuredAnalysis. Analysis is
    derived input to strategy; an explicit recommendation candidate must exist
    before a recommendation can enter downstream consumers.
    """

    @staticmethod
    def produce(candidates: list, evidence: list[dict]) -> list[dict]:
        evidence_ids = {
            item.get("source_id")
            for item in evidence
            if isinstance(item, dict) and item.get("source_id")
        }
        produced: list[dict] = []

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if not isinstance(candidate.get("id"), str) or not candidate["id"].strip():
                continue
            if not isinstance(candidate.get("recommendation"), str) or not candidate["recommendation"].strip():
                continue

            source_ids = candidate.get("evidence_source_ids")
            if not isinstance(source_ids, list) or not source_ids:
                continue
            if not all(
                isinstance(source_id, str) and source_id in evidence_ids
                for source_id in source_ids
            ):
                continue

            provenance = candidate.get("provenance")
            if not isinstance(provenance, dict):
                continue

            try:
                recommendation = Recommendation(
                    id=candidate["id"].strip(),
                    recommendation=candidate["recommendation"].strip(),
                    evidence_source_ids=list(source_ids),
                    action=candidate.get("action"),
                    reply=candidate.get("reply"),
                    priority=candidate.get("priority"),
                    time_horizon=candidate.get("time_horizon"),
                    provenance=dict(provenance),
                )
            except ValueError:
                continue

            produced.append(recommendation.model_dump(mode="json"))

        return produced
