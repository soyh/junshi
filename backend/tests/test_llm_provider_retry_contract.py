import json

import httpx
import pytest
from pydantic import ValidationError

from app.schemas.llm_provider_config import LLMProviderConfigUpdate
from app.services.llm import LLMAnalysisError
from app.services.qwen_provider import QwenProvider


def make_provider(client, *, timeout_seconds=7.5):
    return QwenProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
        timeout_seconds=timeout_seconds,
        client=client,
    )


def test_analysis_uses_configured_timeout_on_http_request():
    def handler(request):
        assert set(request.extensions["timeout"].values()) == {7.5}
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps({})}}]},
        )

    provider = make_provider(httpx.Client(transport=httpx.MockTransport(handler)))

    assert provider.analyze({}) == {}


def test_analysis_timeout_is_not_retried():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("upstream timed out")

    provider = make_provider(httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(LLMAnalysisError, match="request failed"):
        provider.analyze({})

    assert calls == 1


def test_analysis_rate_limit_is_not_retried():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(429, json={"error": {"message": "rate limited"}})

    provider = make_provider(httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(LLMAnalysisError, match="request failed"):
        provider.analyze({})

    assert calls == 1


def test_connection_uses_configured_timeout_and_does_not_retry_timeout():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        assert set(request.extensions["timeout"].values()) == {7.5}
        raise httpx.ReadTimeout("upstream timed out")

    provider = make_provider(httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(LLMAnalysisError, match="connection test failed"):
        provider.test_connection()

    assert calls == 1


def test_connection_rate_limit_is_not_retried():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(429, json={"error": {"message": "rate limited"}})

    provider = make_provider(httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(LLMAnalysisError, match="connection test failed"):
        provider.test_connection()

    assert calls == 1


@pytest.mark.parametrize("timeout_seconds", [0, -1, 300.1])
def test_provider_config_rejects_invalid_timeout_bounds(timeout_seconds):
    with pytest.raises(ValidationError, match="timeout_seconds"):
        LLMProviderConfigUpdate(
            base_url="https://example.test/v1",
            model="test-model",
            api_key="test-key",
            timeout_seconds=timeout_seconds,
        )


def test_provider_config_accepts_maximum_timeout_bound():
    config = LLMProviderConfigUpdate(
        base_url="https://example.test/v1",
        model="test-model",
        api_key="test-key",
        timeout_seconds=300,
    )

    assert config.timeout_seconds == 300
