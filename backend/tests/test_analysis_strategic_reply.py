from app.schemas.structured_analysis import StructuredAnalysis
from app.services.analysis_strategic_reply import AnalysisStrategicReplyService


class FakeAnalysisService:
    def __init__(self):
        self.calls = []

    def get_context(self, conn, user_id, conversation_id):
        self.calls.append((conn, user_id, conversation_id))
        return {"person": {"id": "person-1"}, "conversation": {"id": conversation_id}}


class FakeAnalysisLLMService:
    def __init__(self):
        self.analysis_service = FakeAnalysisService()
        self.calls = []

    def analyze_context(self, context, *, provider=None):
        self.calls.append((context, provider))
        return StructuredAnalysis.model_validate({
            "summary": "derived",
            "observed_facts": [],
            "inferences": [],
            "unknowns": [{"content": "unknown", "confidence": 1.0, "evidence_source_ids": []}],
            "hypotheses": [],
            "emotional_signals": [],
            "relationship_signals": [],
            "risk_signals": [],
            "intent_signals": [],
            "evidence_links": [],
            "analysis_constraints": ["must_preserve_unknowns"],
        })


class FakeReplyService:
    def __init__(self):
        self.calls = []

    def get_context(self, conn, user_id, person_id):
        self.calls.append((conn, user_id, person_id))
        return {
            "person": {"id": person_id},
            "relationship": {"id": "relationship-1"},
            "current_state": {"status": "active", "stage": "dating"},
            "evidence": [],
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [],
            "reply_constraints": {"must_not_auto_send": True},
            "draft": None,
        }


class FakeLearningStrategyBridge:
    def __init__(self):
        self.calls = []

    def get_context(self, conn, user_id, person_id):
        self.calls.append((conn, user_id, person_id))
        return {
            "person": {"id": person_id},
            "relationship": {"id": "relationship-1"},
            "current_state": {"status": "active", "stage": "dating"},
            "evidence": [],
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [],
            "reply_constraints": {"must_not_auto_send": True},
            "draft": None,
            "learning_strategy": {"candidates": []},
        }


class FakeBridge:
    def __init__(self):
        self.calls = []

    def build_context(self, reply_context, structured_analysis):
        self.calls.append((reply_context, structured_analysis))
        return {**reply_context, "structured_analysis": structured_analysis.model_dump(mode="json")}


class FakeProvider:
    pass


def test_orchestration_uses_conversation_analysis_then_person_reply_context():
    llm = FakeAnalysisLLMService()
    reply = FakeReplyService()
    learning_bridge = FakeLearningStrategyBridge()
    bridge = FakeBridge()
    service = AnalysisStrategicReplyService(
        analysis_llm_service=llm,
        strategic_reply_service=reply,
        analysis_bridge_service=bridge,
        learning_strategy_bridge_service=learning_bridge,
    )
    provider = FakeProvider()

    result = service.build_context("conn", "user-1", "conversation-1", provider=provider)

    assert llm.analysis_service.calls == [("conn", "user-1", "conversation-1")]
    assert llm.calls[0][1] is provider
    assert reply.calls == []
    assert learning_bridge.calls == [("conn", "user-1", "person-1")]
    assert len(bridge.calls) == 1
    assert result["structured_analysis"]["summary"] == "derived"
    assert result["learning_strategy"] == {"candidates": []}


def test_orchestration_does_not_persist_or_select_a_reply():
    llm = FakeAnalysisLLMService()
    reply = FakeReplyService()
    learning_bridge = FakeLearningStrategyBridge()
    bridge = FakeBridge()
    service = AnalysisStrategicReplyService(
        analysis_llm_service=llm,
        strategic_reply_service=reply,
        analysis_bridge_service=bridge,
        learning_strategy_bridge_service=learning_bridge,
    )

    result = service.build_context("conn", "user-1", "conversation-1", provider=FakeProvider())

    assert result["draft"] is None
    assert result["recommendations"] == []
    assert result["learning_strategy"] == {"candidates": []}
