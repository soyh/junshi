import sqlite3
from copy import deepcopy
from time import perf_counter
from typing import Any

from app.services.analysis_llm import AnalysisLLMService
from app.services.analysis_recommendation import AnalysisRecommendationService
from app.services.llm import LLMAnalysisError, LatestTurnError
from app.services.strategic_reply import StrategicReplyService
from app.services.strategic_reply_analysis_bridge import StrategicReplyAnalysisBridgeService
from app.services.strategic_reply_learning_strategy_bridge import (
    StrategicReplyLearningStrategyBridgeService,
)
from app.services.strategic_reply_llm import StrategicReplyLLMService

#: Facts the operator registered about themselves; they are authoritative for
#: first-person claims (age, city, job…) and must never be invented otherwise.
PROFILE_FIELDS = ("nickname", "gender", "birth_year", "city", "job", "hobbies",
                  "relationship", "about")


def _stored_profile(conn: sqlite3.Connection, user_id: str):
    """The signed-in user's own facts live on the account, not on each device."""
    # Tests hand in a stub connection; only real sqlite handles have execute().
    if not hasattr(conn, "execute"):
        return None
    try:
        from app.services.user_profile import UserProfileService
        return UserProfileService().get(conn, user_id)
    except Exception:
        # A database without the profile table must not break draft generation.
        return None


def _resolve_profile(conn: sqlite3.Connection, user_id: str, override) -> dict[str, str]:
    cleaned = _clean_profile(override)
    if cleaned:
        return cleaned
    stored = _stored_profile(conn, user_id)
    if stored is None:
        return {}
    from app.services.user_profile import UserProfileService
    return _clean_profile(UserProfileService().prompt_facts(stored))


def _resolve_rules(conn: sqlite3.Connection, user_id: str, override: str) -> str:
    value = (override or "").strip()
    if value:
        return value[:1500]
    stored = _stored_profile(conn, user_id)
    if stored is None:
        return ""
    return str(stored.reply_rules or "").strip()[:1500]


def _clean_profile(raw: dict[str, str] | None) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    cleaned = {}
    for key, value in raw.items():
        name = str(key).strip().lower()
        text = str(value).strip()
        if name in PROFILE_FIELDS and text:
            cleaned[name] = text[:200]
    return cleaned


#: Emoji a person actually types into a chat box (not the whole Unicode set).
CHAT_EMOJI = "😀😄😅🙂😊🥲😂🤣😉😍🤔😎🙃😭😤👍🙏❤️💔🥰😘😏😴🤝👌✨"
MY_STYLE_SAMPLE_LIMIT = 30
MY_STYLE_SAMPLE_MESSAGES = 6


def build_self_style(messages: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Summarise how *this* user writes, from their own past messages.

    Only style is kept (length, rhythm, punctuation and emoji habits, a few
    verbatim samples). Content facts are deliberately excluded: the draft may
    imitate the rhythm but must never replay the samples as new events.
    """
    mine = [
        str(message.get("content") or "").strip()
        for message in messages or []
        if isinstance(message, dict)
        and message.get("sender_type") == "user"
        and str(message.get("content") or "").strip()
    ][-MY_STYLE_SAMPLE_LIMIT:]
    if not mine:
        return {}
    lengths = [len(text) for text in mine]
    emoji_count = sum(1 for text in mine if any(char in text for char in CHAT_EMOJI))
    question_count = sum(
        1 for text in mine if text.rstrip("。.!！~～ ").endswith(("?", "？"))
    )
    exclamation_count = sum(1 for text in mine if any(ch in text for ch in "!！~～"))
    openers: dict[str, int] = {}
    for text in mine:
        head = text[:2]
        if len(head) == 2:
            openers[head] = openers.get(head, 0) + 1
    common = [
        head for head, count in sorted(openers.items(), key=lambda item: -item[1])[:5]
        if count > 1
    ]
    ordered = sorted(lengths)
    return {
        "message_count": len(mine),
        "avg_chars": round(sum(lengths) / len(lengths), 1),
        "median_chars": ordered[len(ordered) // 2],
        "short_share": round(sum(1 for n in lengths if n <= 15) / len(lengths), 2),
        "emoji_share": round(emoji_count / len(mine), 2),
        "question_share": round(question_count / len(mine), 2),
        "exclamation_share": round(exclamation_count / len(mine), 2),
        "uses_period": round(
            sum(1 for text in mine if text.endswith(("。", "."))) / len(mine), 2
        ),
        "common_openers": common,
        "recent_samples": mine[-MY_STYLE_SAMPLE_MESSAGES:],
    }


class AnalysisStrategicReplyService:
    """Orchestrate AnalysisContext → Recommendation → evidence-backed reply draft."""

    RECENT_MESSAGE_LIMIT = 8
    MAX_CORRECTIONS = 3

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
            "model_references": analysis_context.get("model_references"),
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
            raise LatestTurnError("analysis")
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
        progress=None,
        channel_rules: str = "",
        self_profile: dict[str, str] | None = None,
    ) -> dict:
        started = perf_counter()
        timings = {"analysis_seconds": 0.0, "draft_seconds": 0.0,
                   "analysis_attempts": 0, "draft_attempts": 0}
        analysis_context = self.analysis_llm_service.analysis_service.get_context(
            conn, user_id, conversation_id
        )
        person_id = analysis_context["person"]["id"]
        conversation_focus = self._build_conversation_focus(analysis_context)
        llm_analysis_context = dict(analysis_context)
        llm_analysis_context["conversation_focus"] = conversation_focus

        for attempt in range(self.MAX_CORRECTIONS + 1):
            if progress: progress('analysis', attempt + 1)
            phase_started = perf_counter()
            timings["analysis_attempts"] += 1
            structured_analysis = self.analysis_llm_service.analyze_context(
                llm_analysis_context, provider=provider,
            )
            recommendation_context = self.analysis_recommendation_service.build_context(
                conn, user_id, conversation_id, provider=provider,
                structured_analysis=structured_analysis,
            )
            timings["analysis_seconds"] += perf_counter() - phase_started
            try:
                recommendations = self._fresh_recommendations(
                    list(recommendation_context.get("recommendations", []) or []),
                    conversation_focus,
                )
                break
            except LatestTurnError:
                if attempt == self.MAX_CORRECTIONS:
                    raise LatestTurnError("analysis", exhausted=True, corrections=attempt) from None
                llm_analysis_context = deepcopy(llm_analysis_context)
                llm_analysis_context["latest_turn_correction"] = {
                    "stage": "analysis", "attempt": attempt + 1,
                    "reason": "No usable hypothesis supported by the latest reply target survived validation.",
                    "instruction": "Re-analyze the actual latest reply target. Include a useful response hypothesis in hypotheses with its exact canonical message ID in evidence_source_ids. Merely mentioning it in summary or observed_facts is insufficient. Do not attach an ID to an unrelated hypothesis or invent missing facts.",
                }
        evidence = self._focused_evidence(
            recommendation_context,
            analysis_context,
            recommendations,
            conversation_focus,
        )

        generation_context = {
            "person_memory": analysis_context.get("person_memory"),
            "current_state": recommendation_context.get("current_state", {}),
            "evidence": evidence,
            "unknowns": recommendation_context.get("unknowns", []),
            "recommendations": recommendations,
            "model_references": analysis_context.get("model_references"),
            "conversation_focus": conversation_focus,
            "required_evidence_source_ids": conversation_focus.get(
                "required_evidence_source_ids", []
            ),
            "channel_rules": _resolve_rules(conn, user_id, channel_rules),
            "self_profile": _resolve_profile(conn, user_id, self_profile),
            "self_style": build_self_style(analysis_context.get("messages")),
            "constraints": {
                "must_be_evidence_backed": True,
                "must_prioritize_current_conversation": True,
                "must_prioritize_latest_reply_target": True,
                "must_preserve_unknowns": True,
                "must_not_auto_send": True,
                "must_not_auto_execute": True,
                # channel_rules is operator style guidance; it ranks below every
                # safety, provenance and schema rule, but above generic style.
                "channel_rules_scope": "style_first",
                "may_speak_as_user": True,
                "self_profile_scope": "authoritative_personal_facts",
                "self_style_scope": "style_only",
            },
        }
        for attempt in range(self.MAX_CORRECTIONS + 1):
            if progress: progress('draft', attempt + 1)
            phase_started = perf_counter()
            timings["draft_attempts"] += 1
            try:
                generated_reply = self.strategic_reply_llm_service.generate(
                    generation_context, provider=provider,
                )
                timings["draft_seconds"] += perf_counter() - phase_started
                break
            except LatestTurnError:
                timings["draft_seconds"] += perf_counter() - phase_started
                if attempt == self.MAX_CORRECTIONS:
                    raise LatestTurnError("draft", exhausted=True, corrections=attempt) from None
                generation_context = deepcopy(generation_context)
                generation_context["latest_turn_correction"] = {
                    "stage": "draft", "attempt": attempt + 1,
                    "reason": "The draft omitted mandatory latest-turn provenance.",
                    "instruction": "Generate a new reply that answers reply_target_message. Select supporting recommendation IDs and cite its exact canonical message ID in evidence_source_ids. Do not merely relabel the previous draft or invent facts.",
                }
        if generated_reply is None:
            raise LLMAnalysisError("no usable strategic reply draft")
        reply_candidates = [generated_reply] if generated_reply is not None else []

        reply_context = self.strategic_reply_service.build_context_from_recommendation_context(
            recommendation_context,
            reply_candidates=reply_candidates,
            derived=True,
        )
        if not isinstance(reply_context.get("draft"), str) or not reply_context["draft"].strip():
            raise LLMAnalysisError("no usable strategic reply draft")

        learning_context = self.learning_strategy_bridge_service.get_context(
            conn, user_id, person_id
        )
        reply_context["learning_strategy"] = learning_context.get(
            "learning_strategy",
            {"candidates": []},
        )

        result = self.analysis_bridge_service.build_context(
            reply_context,
            structured_analysis,
        )
        result.setdefault("reply_inputs", {})["conversation_focus"] = {
            "conversation_id": conversation_id,
            "latest_human_message": conversation_focus.get("latest_human_message"),
            "reply_target_message": conversation_focus.get("reply_target_message"),
        }
        timings["total_seconds"] = perf_counter() - started
        result["reply_inputs"]["timings"] = timings
        return result
