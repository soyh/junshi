import httpx
import pytest

from app.services.llm import LLMAnalysisError
from app.services.qwen_provider import QwenProvider


def make_client(exception=None, status_code=200, body=None):
    def handler(request):
        if exception is not None:
            raise exception
        return httpx.Response(
            status_code,
            json=body if body is not None else {"choices": [{"message": {"content": "OK"}}]},
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def make_provider(client):
    return QwenProvider(
        api_key="secret-test-key",
        base_url="https://example.test/v1",
        model="example-model",
        timeout_seconds=3.0,
        client=client,
    )


def test_connection_timeout_is_normalized_without_exposing_provider_details():
    provider = make_provider(make_client(httpx.ReadTimeout("upstream timed out")))

    with pytest.raises(LLMAnalysisError) as exc_info:
        provider.test_connection()

    assert str(exc_info.value) == "Qwen provider connection test failed"
    assert "secret-test-key" not in str(exc_info.value)


def test_connection_429_is_normalized_without_exposing_upstream_body():
    provider = make_provider(
        make_client(
            status_code=429,
            body={"error": {"message": "rate limit for secret-test-key"}},
        )
    )

    with pytest.raises(LLMAnalysisError) as exc_info:
        provider.test_connection()

    assert str(exc_info.value) == "Qwen provider connection test failed"
    assert "secret-test-key" not in str(exc_info.value)


def test_connection_malformed_json_is_normalized():
    def handler(request):
        return httpx.Response(
            200,
            content=b"not-json",
            headers={"content-type": "application/json"},
        )

    provider = make_provider(httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(LLMAnalysisError, match="connection test failed"):
        provider.test_connection()
