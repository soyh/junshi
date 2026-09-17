from cryptography.fernet import Fernet

from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.llm_provider_config import LLMProviderConfigService


ENCRYPTION_KEY = Fernet.generate_key().decode("ascii")


def test_user_llm_provider_config_is_scoped_and_key_is_not_returned(client, monkeypatch):
    monkeypatch.setenv("LLM_CONFIG_ENCRYPTION_KEY", ENCRYPTION_KEY)
    get_settings.cache_clear()

    response = client.get(
        "/api/v1/settings/llm",
        headers={"X-User-ID": "user-a"},
    )
    assert response.status_code == 200
    assert response.json() is None

    response = client.put(
        "/api/v1/settings/llm",
        headers={"X-User-ID": "user-a"},
        json={
            "provider": "openai_compatible",
            "base_url": "https://example.test/v1",
            "model": "example-model",
            "api_key": "secret-api-key",
            "timeout_seconds": 45,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "provider": "openai_compatible",
        "base_url": "https://example.test/v1",
        "model": "example-model",
        "timeout_seconds": 45.0,
        "api_key_configured": True,
    }
    assert "api_key" not in body

    response = client.get(
        "/api/v1/settings/llm",
        headers={"X-User-ID": "user-b"},
    )
    assert response.status_code == 200
    assert response.json() is None

    response = client.get(
        "/api/v1/settings/llm",
        headers={"X-User-ID": "user-a"},
    )
    assert response.status_code == 200
    assert response.json()["model"] == "example-model"

    with get_connection() as conn:
        row = conn.execute(
            "SELECT api_key_encrypted FROM user_llm_provider_configs WHERE user_id = ?",
            ("user-a",),
        ).fetchone()
        assert row is not None
        assert row["api_key_encrypted"] != "secret-api-key"

        provider = LLMProviderConfigService().build_provider(conn, "user-a")
        assert provider.api_key == "secret-api-key"
        assert provider.base_url == "https://example.test/v1"
        assert provider.model == "example-model"
        assert provider.timeout_seconds == 45.0

    response = client.delete(
        "/api/v1/settings/llm",
        headers={"X-User-ID": "user-a"},
    )
    assert response.status_code == 204

    response = client.get(
        "/api/v1/settings/llm",
        headers={"X-User-ID": "user-a"},
    )
    assert response.status_code == 200
    assert response.json() is None

    get_settings.cache_clear()
