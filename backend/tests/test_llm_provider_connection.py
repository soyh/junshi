import json

import httpx
import pytest

from app.services.llm import LLMAnalysisError
from app.services.qwen_provider import QwenProvider


def make_connection_client(status_code=200, body=None):
    def handler(request):
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        assert request.headers["content-type"] == "application/json"
        payload = json.loads(request.content)
        assert payload["model"] == "example-model"
        assert payload["max_tokens"] == 8
        assert payload["messages"] == [
            {
                "role": "user",
                "content": "Reply with OK to confirm this API connection test.",
            }
        ]
        return httpx.Response(
            status_code,
            json=body if body is not None else {"choices": [{"message": {"content": "OK"}}]},
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_qwen_provider_connection_test_uses_configured_runtime_parameters():
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="example-model",
        timeout_seconds=12.5,
        client=make_connection_client(),
    )

    provider.test_connection()


def test_qwen_provider_connection_test_translates_http_failure():
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="example-model",
        client=make_connection_client(status_code=401, body={"error": "unauthorized"}),
    )

    with pytest.raises(LLMAnalysisError, match="connection test failed"):
        provider.test_connection()


def test_qwen_provider_connection_test_rejects_empty_choices():
    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="example-model",
        client=make_connection_client(body={"choices": []}),
    )

    with pytest.raises(LLMAnalysisError, match="no choices"):
        provider.test_connection()
