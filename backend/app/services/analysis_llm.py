import sqlite3

from app.schemas.structured_analysis import StructuredAnalysis
from app.services.analysis import AnalysisService
from app.services.llm import LLMAnalysisService, LLMProvider


class AnalysisLLMService:
    """Orchestrates deterministic AnalysisContext into derived StructuredAnalysis."""

    def __init__(
        self,
        analysis_service: AnalysisService | None = None,
        llm_service: LLMAnalysisService | None = None,
    ):
        self.analysis_service = analysis_service or AnalysisService()
        self.llm_service = llm_service

    def analyze(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        *,
        provider: LLMProvider | None = None,
    ) -> StructuredAnalysis:
        context = self.analysis_service.get_context(
            conn,
            user_id,
            conversation_id,
        )
        llm_service = self.llm_service or LLMAnalysisService(provider) if provider else self.llm_service
        if llm_service is None:
            raise ValueError("LLM provider is required")
        return llm_service.analyze(context)
