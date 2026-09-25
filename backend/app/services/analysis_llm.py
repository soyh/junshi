import sqlite3

from app.schemas.structured_analysis import StructuredAnalysis
from app.services.analysis import AnalysisService
from app.services.llm import LLMAnalysisService, LLMProvider
from app.services.model_reference import ModelReferenceService
from app.services.model_reference_context import attach_model_reference_context


class AnalysisLLMService:
    """Orchestrates deterministic AnalysisContext into derived StructuredAnalysis."""

    def __init__(
        self,
        analysis_service: AnalysisService | None = None,
        llm_service: LLMAnalysisService | None = None,
        model_reference_service: ModelReferenceService | None = None,
    ):
        self.analysis_service = analysis_service or AnalysisService()
        self.llm_service = llm_service
        self.model_reference_service = model_reference_service or ModelReferenceService()

    def analyze(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        *,
        provider: LLMProvider | None = None,
    ) -> StructuredAnalysis:
        context = self.analysis_service.get_context(conn, user_id, conversation_id)
        context = attach_model_reference_context(
            self.model_reference_service,
            conn,
            user_id,
            context,
        )
        return self.analyze_context(context, provider=provider)

    def analyze_context(
        self,
        context: dict,
        *,
        provider: LLMProvider | None = None,
    ) -> StructuredAnalysis:
        if self.llm_service is not None:
            llm_service = self.llm_service
        elif provider is not None:
            llm_service = LLMAnalysisService(provider)
        else:
            raise ValueError("LLM provider is required")

        return llm_service.analyze(context)
