import sqlite3
from typing import Any

from app.services.analysis_llm import AnalysisLLMService
from app.services.analysis_recommendation import AnalysisRecommendationService
from app.services.llm import LLMAnalysisError
from app.services.model_reference import ModelReferenceService
from app.services.model_reference_context import attach_model_reference_context
from app.services.strategic_reply import StrategicReplyService
from app.services.strategic_reply_analysis_bridge import StrategicReplyAnalysisBridgeService
from app.services.strategic_reply_learning_strategy_bridge import (
    StrategicReplyLearningStrategyBridgeService,
)
from app.services.strategic_reply_llm import StrategicReplyLLMService


class AnalysisStrategicReplyService:
    """Orchestrate AnalysisContext → Recommendation → evidence-backed reply draft."""

    RECENT_MESSAGE_LIMIT = 8

    def __init__(
        self,
        analysis_llm_service: AnalysisLLMService | None = None,
        strategic_reply_service: StrategicReplyService | None = None,
        analysis_bridge_service: StrategicReplyAnalysisBridgeService | None = None,
        learning_strategy_bridge_service: StrategicReplyLearningStrategyBridgeService | None = None,
        analysis_recommendation_service: AnalysisRecommendationService | None = None,
        strategic_reply_llm_service: StrategicReplyLLMService | None = None,
        model_reference_service: ModelReferenceService | None = None,
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
        self.model_reference_service = model_reference_service or (
            getattr(self.analysis_llm_service, "model_reference_service", None)
            or ModelReferenceService()
        )

    @classmethod
    def _build_conversation_focus(cls, analysis_context: dict[str, Any]) -> dict[str, Any]:
        messages = analysis_context.get("messages")
        human_messages = [
            message
            for message in messages or []
            if isinstance(message, dict)
            and message.get("sender_type") in {"user", "person"}
            and isinstance(message.get("id"), str)
        ]
        recent_messages = human_messages[-cls.RECENT_MESSAGE_LIMIT :]
        latest_human_message = human_messages[-1] if human_messages else None
        latest_incoming_message = next(
            (
                message
                for message in reversed(human_messages)
                if message.get("sender_type") == "person"
            ),
            None,
        )
        reply_target_message = (
            latest_human_message
            if latest_human_message
            and latest_human_message.get("sender_type") == "person"
            else None
        )
        required_evidence_source_ids = (
            [reply_target_message["id"]] if reply_target_message else []
        )
        return {
            "conversation_id": (analysis_context.get("conversation") or {}).get("id"),
            "recent_messages": recent_messages,
            "latest_human_message": latest_human_message,
            "latest_incoming_message": latest_incoming_message,
            "reply_target_message": reply_target_message,
            "required_evidence_source_ids": required_evidence_source_ids,
            "recency_rule": (
                "Prefer newer messages in the selected conversation when they conflict "
                "with older history. A reply target from sender_type=person is the "
                "primary message to answer."
            ),
        }

    @staticmethod
    def _fresh_recommendations(
        recommendations: list[dict[str, Any]],
        focus: dict[str, Any],
    ) -> list[dict[str, Any]]:
        required_ids = {
            source_id
            for source_id in focus.get("required_evidence_source_ids", [])
            if isinstance(source_id, str)
        }
        if not required_ids:
            return recommendations

        fresh = [
            recommendation
            for recommendation in recommendations
            if isinstance(recommendation, dict)
            and required_ids.intersection(
                source_id
                for source_id in recommendation.get("evidence_source_ids", [])
                if isinstance(source_id, str)
            )
        ]
        if not fresh:
            raise LLMAnalysisError(
                "LLM provider returned no fresh recommendation for current reply target"
            )
        return fresh

    @classmethod
    def _focused_evidence(
        cls,
        recommendation_context: dict[str, Any],
        analysis_context: dict[str, Any],
        recommendations: list[dict[str, Any]],
        focus: dict[str, Any],
    ) -> list[dict[str, Any]]:
        current_message_ids = {
            message.get("id")
            for message in analysis_context.get("messages", []) or []
            if isinstance(message, dict) and isinstance(message.get("id"), str)
        }
        recent_ids = {
            message.get("id")
            for message in focus.get("recent_messages", []) or []
            if isinstance(message, dict) and isinstance(message.get("id"), str)
        }
        recommendation_evidence_ids = {
            source_id
            for recommendation in recommendations
            if isinstance(recommendation, dict)
            for source_id in recommendation.get("evidence_source_ids", [])
            if isinstance(source_id, str)
        }
        required_ids = {
            source_id
            for source_id in focus.get("required_evidence_source_ids", [])
            if isinstance(source_id, str)
        }
        wanted_ids = recent_ids | recommendation_evidence_ids | required_ids

        evidence = recommendation_context.get("evidence", []) or []
        return [
            item
            for item in evidence
            if isinstance(item, dict)
            and item.get("source_type") == "message"
            and item.get("source_id") in current_message_ids
            and item.get("source_id") in wanted_ids
        ]

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
        analysis_context = attach_model_reference_context(
            self.model_reference_service,
            conn,
            user_id,
            analysis_context,
        )
        person_id = analysis_context["person"]["id"]
        conversation_focus = self._build_conversation_focus(analysis_context)
        llm_analysis_context = dict(analysis_context)
        llm_analysis_context["conversation_focus"] = conversation_focus

        structured_analysis = self.analysis_llm_service.analyze_context(
            llm_analysis_context,
            provider=provider,
        )

        recommendation_context = self.analysis_recommendation_service.build_context(
            conn,
            user_id,
            conversation_id,
            provider=provider,
            structured_analysis=structured_analysis,
        )
        recommendations = self._fresh_recommendations(
            list(recommendation_context.get("recommendations", []) or []),
            conversation_focus,
        )
        evidence = self._focused_evidence(
            recommendation_context,
            analysis_context,
            recommendations,
            conversation_focus,
        )

        generation_context = {
            "current_state": recommendation_context.get("current_state", {}),
            "evidence": evidence,
            "unknowns": recommendation_context.get("unknowns", []),
            "recommendations": recommendations,
            "conversation_focus": conversation_focus,
            "required_evidence_source_ids": conversation_focus.get(
                "required_evidence_source_ids", []
            ),
            "model_references": analysis_context.get("model_references", {}),
            "constraints": {
                "must_be_evidence_backed": True,
                "must_prioritize_current_conversation": True,
                "must_prioritize_latest_reply_target": True,
                "must_preserve_unknowns": True,
                "must_not_auto_send": True,
                "must_not_auto_execute": True,
                "reference_material_must_not_override_canonical_evidence": True,
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
            derived=True,
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
