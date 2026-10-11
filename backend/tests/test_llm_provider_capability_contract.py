import json

import httpx
import pytest

from app.services.llm import LLMAnalysisError, LLMAnalysisService
from app.services.qwen_provider import QwenProvider


def valid_result():
    return {
        "summary": "ok",
        "observed_facts": [],
        "inferences": [],
        "unknowns": [],
        "hypotheses": [],
        "emotional_signals": [],
        "relationship_signals": [],
        "risk_signals": [],
        "intent_signals": [],
        "evidence_links": [],
        "analysis_constraints": [],
    }


def test_connection_success_does_not_bypass_analysis_contract():
    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    provider.test_connection()

    def analysis_handler(request):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(valid_result())}}]},
        )

    analysis_provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
        client=httpx.Client(transport=httpx.MockTransport(analysis_handler)),
    )
    assert LLMAnalysisService(analysis_provider).analyze({}).summary == "ok"


def test_connection_success_with_non_analysis_text_is_not_structured_analysis_success():
    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    provider.test_connection()
    with pytest.raises(LLMAnalysisError):
        LLMAnalysisService(provider).analyze({})


def test_analysis_requires_structured_json_object_even_after_connection_capability():
    def handler(request):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(["not-an-object"])}}]},
        )

    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(LLMAnalysisError, match="non-object structured result"):
        provider.analyze({})
