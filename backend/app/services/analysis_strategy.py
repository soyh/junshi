import sqlite3

from app.services.analysis_llm import AnalysisLLMService
from app.services.model_reference import ModelReferenceService
from app.services.model_reference_context import attach_model_reference_context
from app.services.strategy_decision import StrategyDecisionContextService


class AnalysisStrategyService:
    """Orchestrates derived analysis into the existing strategy context boundary."""

    def __init__(
        self,
        analysis_llm_service: AnalysisLLMService | None = None,
        strategy_decision_service: StrategyDecisionContextService | None = None,
    ):
        self.analysis_llm_service = analysis_llm_service or AnalysisLLMService()
        self.strategy_decision_service = strategy_decision_service or StrategyDecisionContextService()
        self.model_reference_service = (
            getattr(self.analysis_llm_service, "model_reference_service", None)
            or ModelReferenceService()
        )

    def build_strategy_context(
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
        analysis_context = attach_model_reference_context(
            self.model_reference_service,
            conn,
            user_id,
            analysis_context,
        )
        person_id = analysis_context["person"]["id"]
        structured_analysis = self.analysis_llm_service.analyze_context(
            analysis_context,
            provider=provider,
        )
        return self.strategy_decision_service.get_context(
            conn,
            user_id,
            person_id,
            structured_analysis=structured_analysis,
        )
