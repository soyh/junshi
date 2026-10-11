from cryptography.fernet import Fernet

from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.llm_provider_config import LLMProviderConfigService
from app.services.openai_chat_provider import OpenAICompatibleProvider
from app.services.qwen_provider import QwenProvider


ENCRYPTION_KEY = Fernet.generate_key().decode("ascii")


PROVIDERS = {
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen3.7-flash",
        "provider_type": QwenProvider,
        "strict": True,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-flash",
        "provider_type": OpenAICompatibleProvider,
        "strict": False,
    },
    "kimi": {
        "base_url": "https://api.moonshot.ai/v1",
        "model": "kimi-k2.6",
        "provider_type": OpenAICompatibleProvider,
        "strict": False,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.6-luna",
        "provider_type": OpenAICompatibleProvider,
        "strict": True,
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-3.8-flash",
        "provider_type": OpenAICompatibleProvider,
        "strict": True,
    },
    "openai_compatible": {
        "base_url": "https://gateway.example.test/v1",
        "model": "custom-model",
        "provider_type": OpenAICompatibleProvider,
        "strict": False,
    },
}


def _save(client, user_id: str, provider_name: str, config: dict):
    return client.put(
        "/api/v1/settings/llm",
        headers={"X-User-ID": user_id},
        json={
            "provider": provider_name,
            "base_url": config["base_url"],
            "model": config["model"],
            "api_key": f"secret-{provider_name}",
            "timeout_seconds": 75,
        },
    )


def test_all_supported_providers_are_user_configurable(client, monkeypatch):
    monkeypatch.setenv("LLM_CONFIG_ENCRYPTION_KEY", ENCRYPTION_KEY)
    get_settings.cache_clear()

    service = LLMProviderConfigService()
    for provider_name, config in PROVIDERS.items():
        user_id = f"user-{provider_name}"
        response = _save(client, user_id, provider_name, config)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["provider"] == provider_name
        assert body["base_url"] == config["base_url"]
        assert body["model"] == config["model"]
        assert body["api_key_configured"] is True
        assert "api_key" not in body

        with get_connection() as conn:
            provider = service.build_provider(conn, user_id)

        assert isinstance(provider, config["provider_type"])
        assert provider.api_key == f"secret-{provider_name}"
        assert provider.base_url == config["base_url"]
        assert provider.model == config["model"]
        assert provider.timeout_seconds == 75.0
        assert provider._supports_json_schema() is config["strict"]

    get_settings.cache_clear()


def test_provider_specific_request_options_do_not_leak_qwen_behavior(client, monkeypatch):
    monkeypatch.setenv("LLM_CONFIG_ENCRYPTION_KEY", ENCRYPTION_KEY)
    get_settings.cache_clear()

    service = LLMProviderConfigService()

    response = _save(client, "user-qwen", "qwen", PROVIDERS["qwen"])
    assert response.status_code == 200
    with get_connection() as conn:
        qwen = service.build_provider(conn, "user-qwen")
    assert isinstance(qwen, QwenProvider)
    assert qwen._analysis_request_options() == {"enable_thinking": False}

    for provider_name in ("deepseek", "kimi", "openai", "gemini", "openai_compatible"):
        response = _save(
            client,
            f"user-{provider_name}",
            provider_name,
            PROVIDERS[provider_name],
        )
        assert response.status_code == 200
        with get_connection() as conn:
            provider = service.build_provider(conn, f"user-{provider_name}")
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider._analysis_request_options() == {}

    get_settings.cache_clear()


def test_legacy_dashscope_openai_compatible_config_still_uses_qwen_adapter(
    client,
    monkeypatch,
):
    monkeypatch.setenv("LLM_CONFIG_ENCRYPTION_KEY", ENCRYPTION_KEY)
    get_settings.cache_clear()

    response = client.put(
        "/api/v1/settings/llm",
        headers={"X-User-ID": "legacy-qwen-user"},
        json={
            "provider": "openai_compatible",
            "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            "model": "qwen3.7-flash",
            "api_key": "legacy-secret",
            "timeout_seconds": 60,
        },
    )
    assert response.status_code == 200

    with get_connection() as conn:
        provider = LLMProviderConfigService().build_provider(conn, "legacy-qwen-user")

    assert isinstance(provider, QwenProvider)
    assert provider._analysis_request_options() == {"enable_thinking": False}
    get_settings.cache_clear()


def test_unknown_provider_is_rejected_by_schema(client, monkeypatch):
    monkeypatch.setenv("LLM_CONFIG_ENCRYPTION_KEY", ENCRYPTION_KEY)
    get_settings.cache_clear()

    response = client.put(
        "/api/v1/settings/llm",
        headers={"X-User-ID": "invalid-provider-user"},
        json={
            "provider": "not-a-provider",
            "base_url": "https://example.test/v1",
            "model": "model",
            "api_key": "secret",
            "timeout_seconds": 60,
        },
    )
    assert response.status_code == 422
    get_settings.cache_clear()


def test_product_shell_exposes_multi_provider_byok_presets(client):
    response = client.get("/app")
    assert response.status_code == 200
    html = response.text

    for provider_name in PROVIDERS:
        assert provider_name in html

    assert "Qwen / 阿里云百炼" in html
    assert "DeepSeek" in html
    assert "Kimi / Moonshot" in html
    assert "OpenAI" in html
    assert "Gemini / Google" in html
    assert "其他 OpenAI-compatible" in html
    assert "https://api.deepseek.com" in html
    assert "https://api.moonshot.ai/v1" in html
    assert "https://api.openai.com/v1" in html
    assert "https://generativelanguage.googleapis.com/v1beta/openai" in html
    assert "API Key 仍只在服务端加密保存" in html
