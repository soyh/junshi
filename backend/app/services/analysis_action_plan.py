import sqlite3

from app.services.action_plan import ActionPlanService
from app.services.analysis_llm import AnalysisLLMService


class AnalysisActionPlanService:
    """Project derived StructuredAnalysis into Action Plan without auto-execution."""

    def __init__(
        self,
        analysis_llm_service: AnalysisLLMService | None = None,
        action_plan_service: ActionPlanService | None = None,
    ):
        self.analysis_llm_service = analysis_llm_service or AnalysisLLMService()
        self.action_plan_service = action_plan_service or ActionPlanService()

    def build_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        *,
        provider=None,
    ) -> dict:
        analysis_context = self.analysis_llm_service.analysis_service.get_context(
            conn, user_id, conversation_id
        )
        person_id = analysis_context["person"]["id"]
        structured_analysis = self.analysis_llm_service.analyze_context(
            analysis_context,
            provider=provider,
        )
        action_plan_context = self.action_plan_service.get_context(
            conn, user_id, person_id
        )
        analysis = structured_analysis.model_dump(mode="json")
        result = dict(action_plan_context)
        result["structured_analysis"] = analysis
        result["action_plan_inputs"] = {
            "summary": analysis["summary"],
            "signals": {
                field: list(analysis.get(field) or [])
                for field in (
                    "observed_facts",
                    "inferences",
                    "hypotheses",
                    "emotional_signals",
                    "relationship_signals",
                    "risk_signals",
                    "intent_signals",
                    "unknowns",
                )
            },
            "analysis_is_derived": True,
        }
        result["action_constraints"] = {
            **dict(action_plan_context.get("action_constraints") or {}),
            "must_be_evidence_backed": True,
            "must_preserve_unknowns": True,
            "requires_user_confirmation": True,
            "must_not_auto_execute": True,
            "must_not_change_relationship": True,
            "must_treat_llm_output_as_derived": True,
            "must_preserve_evidence_provenance": True,
        }
        return result
