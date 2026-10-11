import pytest

from app.api.routes.analysis_strategic_reply import _safe_llm_failure_detail
from app.schemas.structured_analysis import StructuredAnalysis
from app.services.analysis_strategic_reply import AnalysisStrategicReplyService
from app.services.llm import LLMAnalysisError
from app.services.qwen_provider import QwenProvider
from app.services.strategic_reply import StrategicReplyService
from app.services.strategic_reply_llm import StrategicReplyLLMService


class FakeAnalysisService:
    def __init__(self):
        self.calls = []

    def get_context(self, conn, user_id, conversation_id):
        self.calls.append((conn, user_id, conversation_id))
        return {
            "person": {"id": "person-1"},
            "conversation": {"id": conversation_id, "person_id": "person-1"},
            "messages": [
                {
                    "id": "message-old-current",
                    "conversation_id": conversation_id,
                    "sender_type": "user",
                    "content": "older current message",
                    "sent_at": "2026-09-21T10:00:00+00:00",
                },
                {
                    "id": "message-latest-person",
                    "conversation_id": conversation_id,
                    "sender_type": "person",
                    "content": "latest incoming message",
                    "sent_at": "2026-09-21T10:01:00+00:00",
                },
            ],
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [],
            "learning_strategy": {},
        }


class FakeAnalysisLLMService:
    def __init__(self):
        self.analysis_service = FakeAnalysisService()
        self.calls = []

    def analyze_context(self, context, *, provider=None):
        self.calls.append((context, provider))
        return StructuredAnalysis.model_validate(
            {
                "summary": "latest message changes the current state",
                "observed_facts": [],
                "inferences": [],
                "unknowns": [],
                "hypotheses": [
                    {
                        "content": "respond to the latest incoming message",
                        "confidence": 0.9,
                        "evidence_source_ids": ["message-latest-person"],
                    }
                ],
                "emotional_signals": [],
                "relationship_signals": [],
                "risk_signals": [],
                "intent_signals": [],
                "evidence_links": [],
                "analysis_constraints": ["prefer latest conversation evidence"],
            }
        )


class FakeAnalysisRecommendationService:
    def __init__(self):
        self.calls = []

    def build_context(
        self,
        conn,
        user_id,
        conversation_id,
        *,
        provider=None,
        structured_analysis=None,
    ):
        self.calls.append(
            (conn, user_id, conversation_id, provider, structured_analysis)
        )
        return {
            "person": {"id": "person-1"},
            "relationship": {"id": "relationship-1"},
            "current_state": {"status": "active", "stage": "dating"},
            "evidence": [
                {
                    "source_id": "message-other-conversation",
                    "source_type": "message",
                    "conversation_id": "conversation-old",
                },
                {
                    "source_id": "message-old-current",
                    "source_type": "message",
                    "conversation_id": conversation_id,
                },
                {
                    "source_id": "message-latest-person",
                    "source_type": "message",
                    "conversation_id": conversation_id,
                },
            ],
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [
                {
                    "id": "recommendation-old",
                    "recommendation": "continue an old topic",
                    "evidence_source_ids": ["message-other-conversation"],
                    "action": None,
                    "reply": None,
                    "priority": None,
                    "time_horizon": None,
                    "provenance": {"source": "strategy_candidate"},
                },
                {
                    "id": "recommendation-latest",
                    "recommendation": "answer the latest incoming message",
                    "evidence_source_ids": ["message-latest-person"],
                    "action": None,
                    "reply": None,
                    "priority": None,
                    "time_horizon": None,
                    "provenance": {"source": "strategy_candidate"},
                },
            ],
        }


class FakeStrategicReplyLLMService:
    def __init__(self):
        self.calls = []

    def generate(self, context, *, provider):
        self.calls.append((context, provider))
        return {
            "recommendation_ids": ["recommendation-latest"],
            "reply": "reply to the newest incoming message",
            "evidence_source_ids": ["message-latest-person"],
        }


class FakeLearningStrategyBridge:
    def get_context(self, conn, user_id, person_id):
        return {
            "learning_strategy": {
                "candidates": [],
                "strategy_decision_learning": {},
                "constraints": {"must_not_auto_send": True},
            }
        }


class FakeBridge:
    def build_context(self, reply_context, structured_analysis):
        return {
            **reply_context,
            "structured_analysis": structured_analysis.model_dump(mode="json"),
        }


class FakeProvider:
    pass


def test_reply_generation_focuses_latest_current_conversation_message():
    analysis_llm = FakeAnalysisLLMService()
    recommendations = FakeAnalysisRecommendationService()
    reply_llm = FakeStrategicReplyLLMService()
    service = AnalysisStrategicReplyService(
        analysis_llm_service=analysis_llm,
        strategic_reply_service=StrategicReplyService(),
        analysis_bridge_service=FakeBridge(),
        learning_strategy_bridge_service=FakeLearningStrategyBridge(),
        analysis_recommendation_service=recommendations,
        strategic_reply_llm_service=reply_llm,
    )

    result = service.build_context(
        "conn",
        "user-1",
        "conversation-current",
        provider=FakeProvider(),
    )

    llm_context = analysis_llm.calls[0][0]
    focus = llm_context["conversation_focus"]
    assert focus["latest_human_message"]["id"] == "message-latest-person"
    assert focus["reply_target_message"]["id"] == "message-latest-person"
    assert focus["required_evidence_source_ids"] == ["message-latest-person"]

    generation_context = reply_llm.calls[0][0]
    assert [item["id"] for item in generation_context["recommendations"]] == [
        "recommendation-latest"
    ]
    assert {
        item["source_id"] for item in generation_context["evidence"]
    } == {"message-old-current", "message-latest-person"}
    assert "message-other-conversation" not in {
        item["source_id"] for item in generation_context["evidence"]
    }
    assert generation_context["required_evidence_source_ids"] == [
        "message-latest-person"
    ]
    assert result["draft"] == "reply to the newest incoming message"


def test_latest_user_message_is_current_state_not_an_unanswered_person_target():
    context = {
        "conversation": {"id": "conversation-1"},
        "messages": [
            {"id": "person-1", "sender_type": "person"},
            {"id": "user-1", "sender_type": "user"},
        ],
    }
    focus = AnalysisStrategicReplyService._build_conversation_focus(context)

    assert focus["latest_human_message"]["id"] == "user-1"
    assert focus["latest_incoming_message"]["id"] == "person-1"
    assert focus["reply_target_message"] is None
    assert focus["required_evidence_source_ids"] == []


def test_fresh_recommendations_refuse_old_topic_when_reply_target_exists():
    focus = {"required_evidence_source_ids": ["message-latest"]}
    with pytest.raises(LLMAnalysisError, match="no fresh recommendation"):
        AnalysisStrategicReplyService._fresh_recommendations(
            [
                {
                    "id": "old",
                    "evidence_source_ids": ["message-old"],
                }
            ],
            focus,
        )


def test_strategic_reply_candidate_must_cite_required_latest_evidence():
    context = {
        "recommendations": [
            {
                "id": "recommendation-1",
                "evidence_source_ids": ["message-old", "message-latest"],
            }
        ],
        "evidence": [
            {"source_id": "message-old", "source_type": "message"},
            {"source_id": "message-latest", "source_type": "message"},
        ],
        "required_evidence_source_ids": ["message-latest"],
    }

    class Provider:
        def generate_strategic_reply(self, payload):
            return {
                "recommendation_ids": ["recommendation-1"],
                "reply": "stale reply",
                "evidence_source_ids": ["message-old"],
            }

    with pytest.raises(LLMAnalysisError, match="stale strategic reply provenance"):
        StrategicReplyLLMService().generate(context, provider=Provider())


def test_qwen_prompts_define_latest_turn_as_primary_reply_focus():
    analysis_prompt = QwenProvider._system_prompt()
    reply_prompt = QwenProvider._strategic_reply_system_prompt()

    assert "latest_human_message" in analysis_prompt
    assert "reply_target_message" in analysis_prompt
    assert "Newer current-conversation evidence takes priority" in analysis_prompt
    assert "reply_target_message" in reply_prompt
    assert "required_evidence_source_ids" in reply_prompt
    assert "continuing an older topic" in reply_prompt


def test_safe_error_category_for_stale_reply_does_not_expose_message_ids():
    assert _safe_llm_failure_detail(
        LLMAnalysisError("LLM provider returned stale strategic reply provenance")
    ) == "LLM analysis failed: latest conversation was not incorporated"
    assert _safe_llm_failure_detail(
        LLMAnalysisError("LLM provider returned no fresh recommendation for current reply target")
    ) == "LLM analysis failed: latest conversation was not incorporated"
