import pytest

from app.services.llm import LLMAnalysisError
from app.services.strategic_reply_llm import StrategicReplyLLMService


class FakeProvider:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate_strategic_reply(self, context):
        self.calls.append(context)
        return self.result


def context():
    return {
        "recommendations": [
            {
                "id": "recommendation-1",
                "recommendation": "Keep the exchange light.",
                "evidence_source_ids": ["message-1", "message-2"],
            }
        ],
        "evidence": [
            {"source_id": "message-1", "source_type": "message"},
            {"source_id": "message-2", "source_type": "message"},
        ],
        "unknowns": [],
    }


def test_generates_reply_only_with_recommendation_and_evidence_provenance():
    provider = FakeProvider(
        {
            "recommendation_ids": ["recommendation-1"],
            "reply": "Sounds good — what are you up to?",
            "evidence_source_ids": ["message-1"],
        }
    )

    result = StrategicReplyLLMService().generate(context(), provider=provider)

    assert result == {
        "recommendation_ids": ["recommendation-1"],
        "reply": "Sounds good — what are you up to?",
        "evidence_source_ids": ["message-1"],
    }
    assert len(provider.calls) == 1


def test_does_not_call_provider_without_recommendations():
    provider = FakeProvider({})
    payload = context()
    payload["recommendations"] = []

    assert StrategicReplyLLMService().generate(payload, provider=provider) is None
    assert provider.calls == []


def test_rejects_unknown_recommendation_provenance():
    provider = FakeProvider(
        {
            "recommendation_ids": ["missing"],
            "reply": "Hello",
            "evidence_source_ids": ["message-1"],
        }
    )

    with pytest.raises(LLMAnalysisError, match="invalid strategic reply provenance"):
        StrategicReplyLLMService().generate(context(), provider=provider)


def test_rejects_evidence_not_cited_by_supporting_recommendation():
    provider = FakeProvider(
        {
            "recommendation_ids": ["recommendation-1"],
            "reply": "Hello",
            "evidence_source_ids": ["message-3"],
        }
    )
    payload = context()
    payload["evidence"].append(
        {"source_id": "message-3", "source_type": "message"}
    )

    with pytest.raises(LLMAnalysisError, match="invalid strategic reply provenance"):
        StrategicReplyLLMService().generate(payload, provider=provider)


def test_rejects_invalid_reply_shape():
    provider = FakeProvider(
        {
            "recommendation_ids": ["recommendation-1"],
            "reply": "",
            "evidence_source_ids": ["message-1"],
        }
    )

    with pytest.raises(LLMAnalysisError, match="invalid strategic reply"):
        StrategicReplyLLMService().generate(context(), provider=provider)
