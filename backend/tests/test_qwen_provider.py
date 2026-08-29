import json

import httpx
import pytest

from app.schemas.structured_analysis import StructuredAnalysis
from app.services.llm import LLMAnalysisError, LLMAnalysisService
from app.services.qwen_provider import QwenProvider


def valid_result():
    return {
        "summary": "A recent conversation signal is present.",
        "observed_facts": [
            {
                "content": "A recent message exists.",
                "confidence": 1.0,
                "evidence_source_ids": ["message-1"],
            }
        ],
        "inferences": [],
        "unknowns": [
            {
                "content": "Current intent is unknown.",
                "confidence": None,
                "evidence_source_ids": [],
            }
        ],
        "hypotheses": [],
        "emotional_signals": [],
        "relationship_signals": [],
        "risk_signals": [],
        "intent_signals": [],
        "evidence_links": [],
        "analysis_constraints": ["LLM output is derived analysis."],
    }


def make_client(content, status_code=200):
    def handler(request):
        assert request.url.path == "/compatible-mode/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "qwen-plus"
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
        return httpx.Response(
            status_code,
            json={
                "choices": [
                    {"message": {"content": content}},
                ]
            },
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_qwen_provider_returns_structured_result():
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        client=make_client(json.dumps(valid_result())),
    )

    result = provider.analyze({"messages": [], "unknowns": []})

    assert result == valid_result()
    assert isinstance(LLMAnalysisService(provider).analyze({"messages": []}), StructuredAnalysis)


def test_qwen_provider_requires_api_key():
    provider = QwenProvider(api_key=None)

    with pytest.raises(LLMAnalysisError, match="API key is not configured"):
        provider.analyze({})


def test_qwen_provider_translates_http_failure():
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        client=make_client({"error": "unavailable"}, status_code=503),
    )

    with pytest.raises(LLMAnalysisError, match="request failed"):
        provider.analyze({})


def test_qwen_provider_translates_malformed_json():
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        client=make_client("not-json"),
    )

    with pytest.raises(LLMAnalysisError, match="request failed"):
        provider.analyze({})


def test_qwen_provider_preserves_provider_result_for_contract_validation():
    malformed = {"summary": "missing contract fields"}
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        client=make_client(json.dumps(malformed)),
    )

    with pytest.raises(LLMAnalysisError, match="invalid structured analysis"):
        LLMAnalysisService(provider).analyze({})
