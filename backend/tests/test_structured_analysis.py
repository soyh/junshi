import pytest
from pydantic import ValidationError

from app.schemas.structured_analysis import StructuredAnalysis
from app.services.llm import LLMAnalysisError, LLMAnalysisService


class FakeProvider:
    def __init__(self, result):
        self.result = result
        self.received_context = None

    def analyze(self, context):
        self.received_context = context
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


def test_llm_service_validates_and_preserves_provenance():
    provider = FakeProvider(valid_result())
    context = {"conversation": {"id": "conversation-1"}, "messages": []}

    result = LLMAnalysisService(provider).analyze(context)

    assert isinstance(result, StructuredAnalysis)
    assert result.inferences[0].evidence_source_ids == ["message-1", "interaction-1"]
    assert provider.received_context is context


def test_llm_service_rejects_malformed_provider_output():
    provider = FakeProvider({"summary": "missing required contract fields"})

    with pytest.raises(LLMAnalysisError):
        LLMAnalysisService(provider).analyze({})


def test_structured_analysis_rejects_unknown_fields():
    payload = valid_result()
    payload["unexpected"] = "must not leak into the contract"

    with pytest.raises(ValidationError):
        StructuredAnalysis.model_validate(payload)


def test_structured_analysis_rejects_invalid_confidence():
    payload = valid_result()
    payload["inferences"][0]["confidence"] = 1.5

    with pytest.raises(ValidationError):
        StructuredAnalysis.model_validate(payload)
