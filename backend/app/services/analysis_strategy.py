import sqlite3

from app.schemas.structured_analysis import StructuredAnalysis
from app.services.analysis_llm import AnalysisLLMService
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

    def build_strategy_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        *,
        provider=None,
    ) -> dict:
        analysis = self.analysis_llm_service.analysis_service.get_context(
            conn, user_id, conversation_id
        )
        person_id = analysis["person"]["id"]
        structured_analysis: StructuredAnalysis = self.analysis_llm_service.analyze(
            conn, user_id, conversation_id, provider=provider
        )
        return self.strategy_decision_service.get_context(
            conn,
            user_id,
            person_id,
            structured_analysis=structured_analysis,
        )
