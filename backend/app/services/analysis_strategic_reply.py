import sqlite3

from app.services.analysis_llm import AnalysisLLMService
from app.services.strategic_reply import StrategicReplyService
from app.services.strategic_reply_analysis_bridge import StrategicReplyAnalysisBridgeService


class AnalysisStrategicReplyService:
    """Orchestrate AnalysisContext → StructuredAnalysis → Strategic Reply context."""

    def __init__(
        self,
        analysis_llm_service: AnalysisLLMService | None = None,
        strategic_reply_service: StrategicReplyService | None = None,
        analysis_bridge_service: StrategicReplyAnalysisBridgeService | None = None,
    ):
        self.analysis_llm_service = analysis_llm_service or AnalysisLLMService()
        self.strategic_reply_service = strategic_reply_service or StrategicReplyService()
        self.analysis_bridge_service = (
            analysis_bridge_service or StrategicReplyAnalysisBridgeService()
        )

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
        reply_context = self.strategic_reply_service.get_context(
            conn, user_id, person_id
        )
        return self.analysis_bridge_service.build_context(
            reply_context,
            structured_analysis,
        )
