import sqlite3

from app.services.analysis_llm import AnalysisLLMService
from app.services.analysis_recommendation import AnalysisRecommendationService
from app.services.strategic_reply import StrategicReplyService
from app.services.strategic_reply_analysis_bridge import StrategicReplyAnalysisBridgeService
from app.services.strategic_reply_learning_strategy_bridge import (
    StrategicReplyLearningStrategyBridgeService,
)
from app.services.strategic_reply_llm import StrategicReplyLLMService


class AnalysisStrategicReplyService:
    """Orchestrate AnalysisContext → Recommendation → evidence-backed reply draft."""

    def __init__(
        self,
        analysis_llm_service: AnalysisLLMService | None = None,
        strategic_reply_service: StrategicReplyService | None = None,
        analysis_bridge_service: StrategicReplyAnalysisBridgeService | None = None,
        learning_strategy_bridge_service: StrategicReplyLearningStrategyBridgeService | None = None,
        analysis_recommendation_service: AnalysisRecommendationService | None = None,
        strategic_reply_llm_service: StrategicReplyLLMService | None = None,
    ):
        self.analysis_llm_service = analysis_llm_service or AnalysisLLMService()
        self.strategic_reply_service = strategic_reply_service or StrategicReplyService()
        self.analysis_bridge_service = (
            analysis_bridge_service or StrategicReplyAnalysisBridgeService()
        )
        self.learning_strategy_bridge_service = (
            learning_strategy_bridge_service
            or StrategicReplyLearningStrategyBridgeService(
                strategic_reply_service=self.strategic_reply_service,
            )
        )
        self.analysis_recommendation_service = (
            analysis_recommendation_service
            or AnalysisRecommendationService(
                analysis_llm_service=self.analysis_llm_service,
            )
        )
        self.strategic_reply_llm_service = (
            strategic_reply_llm_service or StrategicReplyLLMService()
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

        recommendation_context = self.analysis_recommendation_service.build_context(
            conn,
            user_id,
            conversation_id,
            provider=provider,
            structured_analysis=structured_analysis,
        )

        generation_context = {
            "current_state": recommendation_context.get("current_state", {}),
            "evidence": recommendation_context.get("evidence", []),
            "unknowns": recommendation_context.get("unknowns", []),
            "recommendations": recommendation_context.get("recommendations", []),
            "constraints": {
                "must_be_evidence_backed": True,
                "must_preserve_unknowns": True,
                "must_not_auto_send": True,
                "must_not_auto_execute": True,
            },
        }
        generated_reply = self.strategic_reply_llm_service.generate(
            generation_context,
            provider=provider,
        )
        reply_candidates = [generated_reply] if generated_reply is not None else []

        reply_context = self.strategic_reply_service.build_context_from_recommendation_context(
            recommendation_context,
            reply_candidates=reply_candidates,
        )

        learning_context = self.learning_strategy_bridge_service.get_context(
            conn, user_id, person_id
        )
        reply_context["learning_strategy"] = learning_context.get(
            "learning_strategy",
            {"candidates": []},
        )

        return self.analysis_bridge_service.build_context(
            reply_context,
            structured_analysis,
        )
