from app.schemas.structured_analysis import StructuredAnalysis


class StrategyAnalysisBridgeService:
    """Builds strategy input from derived analysis without changing canonical context."""

    _DECISION_SIGNAL_FIELDS = (
        "observed_facts",
        "inferences",
        "hypotheses",
        "emotional_signals",
        "relationship_signals",
        "risk_signals",
        "intent_signals",
        "unknowns",
    )

    def build_input(
        self,
        strategy_context: dict,
        structured_analysis: StructuredAnalysis,
    ) -> dict:
        if not isinstance(strategy_context, dict):
            raise TypeError("strategy_context must be a dict")

        result = dict(strategy_context)
        analysis = structured_analysis.model_dump(mode="json")
        result["structured_analysis"] = analysis
        result["decision_inputs"] = self._decision_inputs(
            strategy_context.get("decision_inputs"), analysis
        )
        result["strategy_constraints"] = {
            **dict(strategy_context.get("strategy_constraints") or {}),
            "must_treat_llm_output_as_derived": True,
            "must_preserve_evidence_provenance": True,
            "must_preserve_unknowns": True,
            "must_not_auto_select": True,
        }
        return result

    def _decision_inputs(self, decision_inputs, analysis: dict) -> dict:
        result = dict(decision_inputs or {})
        result["structured_analysis"] = {
            field: list(analysis.get(field) or [])
            for field in self._DECISION_SIGNAL_FIELDS
        }
        result["analysis_is_derived"] = True
        result["selection_status"] = result.get(
            "selection_status", "requires_explicit_decision"
        )
        return result
