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


def _assert_response_format(payload, *, model, schema_name):
    if model.startswith(("qwen3.7", "qwen3.8")):
        response_format = payload["response_format"]
        assert response_format["type"] == "json_schema"
        json_schema = response_format["json_schema"]
        assert json_schema["name"] == schema_name
        assert json_schema["strict"] is True
        assert json_schema["schema"]["type"] == "object"
        assert "properties" in json_schema["schema"]
    else:
        assert payload["response_format"] == {"type": "json_object"}


def make_client(
    content,
    status_code=200,
    *,
    model="qwen-plus",
    expected_enable_thinking=None,
):
    def handler(request):
        assert request.url.path == "/compatible-mode/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["model"] == model
        _assert_response_format(payload, model=model, schema_name="structured_analysis")
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
        if expected_enable_thinking is None:
            assert "enable_thinking" not in payload
        else:
            assert payload["enable_thinking"] is expected_enable_thinking
        return httpx.Response(
            status_code,
            json={
                "choices": [
                    {"message": {"content": content}},
                ]
            },
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def make_reply_client(content, *, model="qwen3.8-flash"):
    def handler(request):
        assert request.url.path == "/compatible-mode/v1/chat/completions"
        payload = json.loads(request.content)
        assert payload["model"] == model
        _assert_response_format(payload, model=model, schema_name="strategic_reply")
        assert payload["enable_thinking"] is False
        assert "recommendation_ids" in payload["messages"][0]["content"]
        assert "evidence_source_ids" in payload["messages"][0]["content"]
        assert "recommendations" in payload["messages"][1]["content"]
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
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


def test_qwen37_structured_analysis_uses_strict_schema_and_disables_thinking():
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        model="qwen3.7-flash",
        client=make_client(
            json.dumps(valid_result()),
            model="qwen3.7-flash",
            expected_enable_thinking=False,
        ),
    )

    result = provider.analyze({"messages": [], "unknowns": []})

    assert result == valid_result()


def test_qwen38_structured_analysis_uses_strict_schema_and_disables_thinking():
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        model="qwen3.8-flash",
        client=make_client(
            json.dumps(valid_result()),
            model="qwen3.8-flash",
            expected_enable_thinking=False,
        ),
    )

    result = provider.analyze({"messages": [], "unknowns": []})

    assert result == valid_result()


def test_qwen37_strategic_reply_uses_strict_schema_and_disables_thinking():
    expected = {
        "recommendation_ids": ["recommendation-1"],
        "reply": "What are you up to?",
        "evidence_source_ids": ["message-1"],
    }
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        model="qwen3.7-flash",
        client=make_reply_client(json.dumps(expected), model="qwen3.7-flash"),
    )

    result = provider.generate_strategic_reply(
        {
            "recommendations": [
                {
                    "id": "recommendation-1",
                    "evidence_source_ids": ["message-1"],
                }
            ],
            "evidence": [{"source_id": "message-1"}],
        }
    )

    assert result == expected


def test_qwen38_strategic_reply_uses_strict_schema_and_disables_thinking():
    expected = {
        "recommendation_ids": ["recommendation-1"],
        "reply": "What are you up to?",
        "evidence_source_ids": ["message-1"],
    }
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        model="qwen3.8-flash",
        client=make_reply_client(json.dumps(expected)),
    )

    result = provider.generate_strategic_reply(
        {
            "recommendations": [
                {
                    "id": "recommendation-1",
                    "evidence_source_ids": ["message-1"],
                }
            ],
            "evidence": [{"source_id": "message-1"}],
        }
    )

    assert result == expected


def test_qwen37_falls_back_to_json_object_when_endpoint_rejects_json_schema():
    calls = []

    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload["response_format"]["type"])
        if len(calls) == 1:
            assert payload["response_format"]["type"] == "json_schema"
            return httpx.Response(
                400,
                json={"message": "response_format json_schema is not supported in this region"},
            )
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["enable_thinking"] is False
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(valid_result())}}]},
        )

    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        model="qwen3.7-flash",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert provider.analyze({"messages": []}) == valid_result()
    assert calls == ["json_schema", "json_object"]


def test_analysis_service_normalizes_only_lossless_shape_drift():
    drifted = valid_result()
    drifted["unknowns"] = None
    drifted["analysis_constraints"] = {
        "must_preserve_unknowns": True,
        "must_treat_llm_output_as_derived": True,
    }
    drifted["observed_facts"] = drifted["observed_facts"][0]

    class Provider:
        def analyze(self, context):
            return drifted

    result = LLMAnalysisService(Provider()).analyze({})

    assert result.unknowns == []
    assert len(result.observed_facts) == 1
    assert result.observed_facts[0].action is None
    assert result.analysis_constraints == [
        "must_preserve_unknowns: true",
        "must_treat_llm_output_as_derived: true",
    ]


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


def test_qwen_provider_preserves_required_field_validation_and_reports_paths():
    malformed = {"summary": "missing contract fields"}
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/compatible-mode/v1",
        client=make_client(json.dumps(malformed)),
    )

    with pytest.raises(
        LLMAnalysisError,
        match=r"invalid structured analysis fields=.*observed_facts",
    ):
        LLMAnalysisService(provider).analyze({})
