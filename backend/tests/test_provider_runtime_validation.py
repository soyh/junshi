import httpx

from app.api.routes import llm_provider_config as route_module
from app.schemas.llm_provider_config import LLMProviderValidationResult
from app.services.llm_provider_config import LLMProviderConfigService
from app.services.openai_chat_provider import OpenAICompatibleProvider


class _Repo:
    def __init__(self, provider="openai", model="gpt-test"):
        self.row = {
            "provider": provider,
            "model": model,
        }

    def get(self, conn, user_id):
        return self.row


def _provider(handler):
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    return OpenAICompatibleProvider(
        api_key="secret-value-never-return",
        base_url="https://provider.example/v1",
        model="gpt-test",
        timeout_seconds=5,
        provider_name="OpenAI",
        supports_json_schema=True,
        client=client,
    )


def _run(monkeypatch, handler):
    service = LLMProviderConfigService(repository=_Repo())
    provider = _provider(handler)
    monkeypatch.setattr(service, "build_provider", lambda conn, user_id: provider)
    result = service.test_connection(None, "user-a")
    assert "secret-value-never-return" not in result.model_dump_json()
    return result


def test_runtime_validation_success(monkeypatch):
    result = _run(
        monkeypatch,
        lambda request: httpx.Response(
            200,
            json={"choices": [{"message": {"content": "OK"}}]},
            request=request,
        ),
    )
    assert result.status == "ok"
    assert result.code == "ok"
    assert result.provider == "openai"
    assert result.model == "gpt-test"


def test_runtime_validation_classifies_api_key(monkeypatch):
    result = _run(
        monkeypatch,
        lambda request: httpx.Response(401, text="invalid api key", request=request),
    )
    assert result.status == "error"
    assert result.code == "api_key_invalid"


def test_runtime_validation_classifies_model(monkeypatch):
    result = _run(
        monkeypatch,
        lambda request: httpx.Response(404, text="model not found", request=request),
    )
    assert result.code == "model_invalid"


def test_runtime_validation_classifies_endpoint(monkeypatch):
    result = _run(
        monkeypatch,
        lambda request: httpx.Response(404, text="not found", request=request),
    )
    assert result.code == "endpoint_invalid"


def test_runtime_validation_classifies_rate_limit(monkeypatch):
    result = _run(
        monkeypatch,
        lambda request: httpx.Response(429, text="too many requests", request=request),
    )
    assert result.code == "rate_limited"


def test_runtime_validation_classifies_provider_unavailable(monkeypatch):
    result = _run(
        monkeypatch,
        lambda request: httpx.Response(503, text="upstream down", request=request),
    )
    assert result.code == "provider_unavailable"


def test_runtime_validation_classifies_malformed_response(monkeypatch):
    result = _run(
        monkeypatch,
        lambda request: httpx.Response(200, json={"unexpected": True}, request=request),
    )
    assert result.code == "malformed_response"


def test_runtime_validation_classifies_timeout(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    result = _run(monkeypatch, handler)
    assert result.code == "timeout"


def test_runtime_validation_route_returns_contract_without_secret(client, monkeypatch):
    result = LLMProviderValidationResult(
        status="error",
        code="model_invalid",
        provider="openai",
        model="gpt-test",
        message="Configured model was rejected by the provider.",
    )
    monkeypatch.setattr(route_module.service, "test_connection", lambda conn, user_id: result)

    response = client.post(
        "/api/v1/settings/llm/test",
        headers={"X-User-ID": "user-a"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body == result.model_dump()
    assert "api_key" not in body
    assert "secret" not in response.text.lower()
