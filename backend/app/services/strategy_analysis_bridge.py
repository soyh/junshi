from app.schemas.structured_analysis import StructuredAnalysis


class StrategyAnalysisBridgeService:
    """Builds strategy input from derived analysis without changing canonical context."""

    def build_input(
        self,
        strategy_context: dict,
        structured_analysis: StructuredAnalysis,
    ) -> dict:
        if not isinstance(strategy_context, dict):
            raise TypeError("strategy_context must be a dict")

        result = dict(strategy_context)
        result["structured_analysis"] = structured_analysis.model_dump(mode="json")
        result["strategy_constraints"] = {
            **dict(strategy_context.get("strategy_constraints") or {}),
            "must_treat_llm_output_as_derived": True,
            "must_preserve_evidence_provenance": True,
            "must_preserve_unknowns": True,
            "must_not_auto_select": True,
        }
        return result
