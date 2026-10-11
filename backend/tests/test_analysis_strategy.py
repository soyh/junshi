from app.schemas.structured_analysis import StructuredAnalysis
from app.services.analysis_strategy import AnalysisStrategyService


class FakeAnalysisService:
    def get_context(self, conn, user_id, conversation_id):
        return {
            "person": {"id": "person-1"},
            "conversation": {"id": conversation_id},
            "messages": [],
        }


class FakeAnalysisLLMService:
    def __init__(self):
        self.analysis_service = FakeAnalysisService()
        self.calls = []

    def analyze_context(self, context, *, provider=None):
        self.calls.append((context, provider))
        return StructuredAnalysis(
            summary="derived",
            observed_facts=[],
            inferences=[
                {
                    "content": "derived inference",
                    "confidence": 0.7,
                    "evidence_source_ids": ["message-1"],
                }
            ],
            unknowns=[{"content": "unknown", "evidence_source_ids": []}],
            hypotheses=[],
            emotional_signals=[],
            relationship_signals=[],
            risk_signals=[],
            intent_signals=[],
            evidence_links=[{"source_id": "message-1"}],
            analysis_constraints=["derived_only"],
        )


class FakeStrategyDecisionService:
    def __init__(self):
        self.calls = []

    def get_context(self, conn, user_id, person_id, *, structured_analysis=None):
        self.calls.append((user_id, person_id, structured_analysis))
        return {
            "person": {"id": person_id},
            "structured_analysis": structured_analysis.model_dump(mode="json"),
            "strategy_constraints": {"must_not_auto_select": True},
        }


def test_orchestrator_flows_analysis_context_into_strategy():
    llm = FakeAnalysisLLMService()
    strategy = FakeStrategyDecisionService()
    service = AnalysisStrategyService(llm, strategy)

    provider = object()
    result = service.build_strategy_context(
        object(),
        "user-1",
        "conversation-1",
        provider=provider,
    )

    assert llm.calls[0][0]["person"]["id"] == "person-1"
    assert llm.calls[0][1] is provider
    assert strategy.calls[0][0:2] == ("user-1", "person-1")
    analysis = strategy.calls[0][2]
    assert analysis.summary == "derived"
    assert analysis.inferences[0].evidence_source_ids == ["message-1"]
    assert result["structured_analysis"]["summary"] == "derived"


def test_orchestrator_does_not_make_structured_analysis_canonical():
    llm = FakeAnalysisLLMService()
    strategy = FakeStrategyDecisionService()
    service = AnalysisStrategyService(llm, strategy)

    service.build_strategy_context(object(), "user-1", "conversation-1")

    context = llm.calls[0][0]
    assert context["person"] == {"id": "person-1"}
    assert "structured_analysis" not in context
