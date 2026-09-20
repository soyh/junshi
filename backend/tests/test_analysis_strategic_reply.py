from app.schemas.structured_analysis import StructuredAnalysis
from app.services.analysis_strategic_reply import AnalysisStrategicReplyService
from app.services.strategic_reply import StrategicReplyService


class FakeAnalysisService:
    def __init__(self):
        self.calls = []

    def get_context(self, conn, user_id, conversation_id):
        self.calls.append((conn, user_id, conversation_id))
        return {
            "person": {"id": "person-1"},
            "conversation": {"id": conversation_id},
        }


class FakeAnalysisLLMService:
    def __init__(self):
        self.analysis_service = FakeAnalysisService()
        self.calls = []

    def analyze_context(self, context, *, provider=None):
        self.calls.append((context, provider))
        return StructuredAnalysis.model_validate(
            {
                "summary": "derived",
                "observed_facts": [],
                "inferences": [],
                "unknowns": [
                    {
                        "content": "unknown",
                        "confidence": 1.0,
                        "evidence_source_ids": [],
                    }
                ],
                "hypotheses": [],
                "emotional_signals": [],
                "relationship_signals": [],
                "risk_signals": [],
                "intent_signals": [],
                "evidence_links": [],
                "analysis_constraints": ["must_preserve_unknowns"],
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
                {"source_id": "message-1", "source_type": "message"},
            ],
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [
                {
                    "id": "recommendation-1",
                    "recommendation": "Keep the exchange light.",
                    "evidence_source_ids": ["message-1"],
                    "action": None,
                    "reply": None,
                    "priority": None,
                    "time_horizon": None,
                    "provenance": {"source": "strategy_candidate"},
                }
            ],
        }


class FakeStrategicReplyLLMService:
    def __init__(self):
        self.calls = []

    def generate(self, context, *, provider):
        self.calls.append((context, provider))
        return {
            "recommendation_ids": ["recommendation-1"],
            "reply": "What are you up to?",
            "evidence_source_ids": ["message-1"],
        }


class FakeLearningStrategyBridge:
    def __init__(self):
        self.calls = []

    def get_context(self, conn, user_id, person_id):
        self.calls.append((conn, user_id, person_id))
        return {
            "learning_strategy": {
                "candidates": [],
                "strategy_decision_learning": {},
                "constraints": {"must_not_auto_send": True},
            }
        }


class FakeBridge:
    def __init__(self):
        self.calls = []

    def build_context(self, reply_context, structured_analysis):
        self.calls.append((reply_context, structured_analysis))
        return {
            **reply_context,
            "structured_analysis": structured_analysis.model_dump(mode="json"),
        }


class FakeProvider:
    pass


def build_service():
    llm = FakeAnalysisLLMService()
    recommendations = FakeAnalysisRecommendationService()
    reply_llm = FakeStrategicReplyLLMService()
    learning_bridge = FakeLearningStrategyBridge()
    bridge = FakeBridge()
    service = AnalysisStrategicReplyService(
        analysis_llm_service=llm,
        strategic_reply_service=StrategicReplyService(),
        analysis_bridge_service=bridge,
        learning_strategy_bridge_service=learning_bridge,
        analysis_recommendation_service=recommendations,
        strategic_reply_llm_service=reply_llm,
    )
    return service, llm, recommendations, reply_llm, learning_bridge, bridge


def test_orchestration_reuses_structured_analysis_for_recommendation_then_reply():
    service, llm, recommendations, reply_llm, learning_bridge, bridge = build_service()
    provider = FakeProvider()

    result = service.build_context(
        "conn",
        "user-1",
        "conversation-1",
        provider=provider,
    )

    assert llm.analysis_service.calls == [("conn", "user-1", "conversation-1")]
    assert llm.calls[0][1] is provider
    assert recommendations.calls[0][0:4] == (
        "conn",
        "user-1",
        "conversation-1",
        provider,
    )
    assert recommendations.calls[0][4] is llm.calls[0][0] or isinstance(
        recommendations.calls[0][4], StructuredAnalysis
    )
    assert reply_llm.calls[0][1] is provider
    assert reply_llm.calls[0][0]["recommendations"][0]["id"] == "recommendation-1"
    assert learning_bridge.calls == [("conn", "user-1", "person-1")]
    assert len(bridge.calls) == 1
    assert result["draft"] == "What are you up to?"
    assert len(result["recommendations"]) == 1
    assert result["structured_analysis"]["summary"] == "derived"


def test_explicit_generation_does_not_send_persist_confirm_or_execute():
    service, _, _, _, _, _ = build_service()

    result = service.build_context(
        "conn",
        "user-1",
        "conversation-1",
        provider=FakeProvider(),
    )

    assert result["draft"] == "What are you up to?"
    assert result["reply_constraints"]["must_not_auto_send"] is True
    assert result["reply_constraints"]["must_treat_llm_output_as_derived"] is True
    assert result["learning_strategy"]["constraints"]["must_not_auto_send"] is True
