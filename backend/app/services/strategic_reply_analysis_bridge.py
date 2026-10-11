from app.schemas.structured_analysis import StructuredAnalysis


class StrategicReplyAnalysisBridgeService:
    """Project derived analysis into Strategic Reply without generating or sending a reply."""

    _REPLY_SIGNAL_FIELDS = (
        "observed_facts",
        "inferences",
        "hypotheses",
        "emotional_signals",
        "relationship_signals",
        "risk_signals",
        "intent_signals",
        "unknowns",
    )

    def build_context(
        self,
        reply_context: dict,
        structured_analysis: StructuredAnalysis,
    ) -> dict:
        if not isinstance(reply_context, dict):
            raise TypeError("reply_context must be a dict")

        result = dict(reply_context)
        analysis = structured_analysis.model_dump(mode="json")
        result["structured_analysis"] = analysis
        result["reply_inputs"] = {
            "summary": analysis["summary"],
            "signals": {
                field: list(analysis.get(field) or [])
                for field in self._REPLY_SIGNAL_FIELDS
            },
            "analysis_is_derived": True,
        }
        result["reply_constraints"] = {
            **dict(reply_context.get("reply_constraints") or {}),
            "must_be_evidence_backed": True,
            "must_preserve_unknowns": True,
            "must_preserve_evidence_provenance": True,
            "must_treat_llm_output_as_derived": True,
            "must_not_auto_send": True,
            "must_not_change_relationship": True,
        }
        return result
