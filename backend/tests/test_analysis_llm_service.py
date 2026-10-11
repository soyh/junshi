import sqlite3

import pytest

from app.schemas.structured_analysis import StructuredAnalysis
from app.services.analysis_llm import AnalysisLLMService
from app.services.llm import LLMAnalysisError, LLMAnalysisService


class FakeAnalysisService:
    def __init__(self, context):
        self.context = context
        self.calls = []

    def get_context(self, conn, user_id, conversation_id):
        self.calls.append((conn, user_id, conversation_id))
        return self.context


class FakeProvider:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.received_context = None

    def analyze(self, context):
        self.received_context = context
        if self.error is not None:
            raise self.error
        return self.result


def valid_result():
    return {
        "summary": "The conversation contains a recent meeting signal.",
        "observed_facts": [
            {
                "content": "The person said they met today.",
                "confidence": 1.0,
                "evidence_source_ids": ["message-1"],
            }
        ],
        "inferences": [
            {
                "content": "A positive interaction may have occurred.",
                "confidence": 0.7,
                "evidence_source_ids": ["message-1", "interaction-1"],
            }
        ],
        "unknowns": [
            {
                "content": "The person's current intent is not established.",
                "evidence_source_ids": [],
            }
        ],
        "hypotheses": [],
        "emotional_signals": [],
        "relationship_signals": [],
        "risk_signals": [],
        "intent_signals": [],
        "evidence_links": [],
        "analysis_constraints": ["Do not treat inference as canonical fact."],
    }


def test_analysis_llm_service_maps_context_to_structured_analysis():
    context = {
        "conversation": {"id": "conversation-1"},
        "messages": [],
        "unknowns": [{"content": "intent unknown"}],
    }
    provider = FakeProvider(valid_result())
    analysis_service = FakeAnalysisService(context)
    service = AnalysisLLMService(
        analysis_service=analysis_service,
        llm_service=LLMAnalysisService(provider),
    )
    conn = sqlite3.connect(":memory:")

    result = service.analyze(conn, "user-1", "conversation-1")

    assert isinstance(result, StructuredAnalysis)
    assert provider.received_context is context
    assert analysis_service.calls == [(conn, "user-1", "conversation-1")]
    assert result.unknowns[0].content == "The person's current intent is not established."


def test_analysis_llm_service_does_not_replace_context_with_provider_output():
    context = {"conversation": {"id": "conversation-1"}, "messages": []}
    provider = FakeProvider(valid_result())
    analysis_service = FakeAnalysisService(context)
    service = AnalysisLLMService(
        analysis_service=analysis_service,
        llm_service=LLMAnalysisService(provider),
    )

    result = service.analyze(sqlite3.connect(":memory:"), "user-1", "conversation-1")

    assert provider.received_context is context
    assert result.summary != context.get("summary")
    assert analysis_service.context is context


def test_analysis_llm_service_requires_provider_when_not_injected():
    service = AnalysisLLMService(analysis_service=FakeAnalysisService({}))

    with pytest.raises(ValueError, match="LLM provider is required"):
        service.analyze(sqlite3.connect(":memory:"), "user-1", "conversation-1")


def test_provider_failure_is_translated_to_llm_analysis_error():
    provider = FakeProvider(error=RuntimeError("provider unavailable"))

    with pytest.raises(LLMAnalysisError, match="LLM provider failed"):
        LLMAnalysisService(provider).analyze({})
