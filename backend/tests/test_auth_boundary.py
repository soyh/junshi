from app.config.settings import get_settings
from app.core.logging import redact_sensitive_text


def _configure_production(
    monkeypatch,
    *,
    token: str | None = "server-secret-token",
    bootstrap_enabled: bool = False,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "AUTH_BOOTSTRAP_ENABLED",
        "true" if bootstrap_enabled else "false",
    )
    if token is None:
        monkeypatch.delenv("AUTH_BEARER_TOKEN", raising=False)
    else:
        monkeypatch.setenv("AUTH_BEARER_TOKEN", token)
    get_settings.cache_clear()


def test_production_requires_bearer_token(client, monkeypatch):
    try:
        _configure_production(monkeypatch)
        response = client.get("/api/v1/settings/llm")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
        assert response.json()["detail"] == "bearer token required"
    finally:
        get_settings.cache_clear()


def test_production_rejects_legacy_x_user_id(client, monkeypatch):
    try:
        _configure_production(monkeypatch)
        response = client.get(
            "/api/v1/settings/llm",
            headers={"X-User-ID": "attacker-controlled-user"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "X-User-ID is not accepted in production"
    finally:
        get_settings.cache_clear()


def test_production_rejects_wrong_bearer_token_without_echoing_it(client, monkeypatch):
    try:
        _configure_production(monkeypatch)
        response = client.get(
            "/api/v1/settings/llm",
            headers={"Authorization": "Bearer attacker-secret"},
        )
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
        assert "attacker-secret" not in response.text
    finally:
        get_settings.cache_clear()


def test_production_accepts_explicitly_enabled_bootstrap_bearer_token(client, monkeypatch):
    try:
        _configure_production(monkeypatch, bootstrap_enabled=True)
        response = client.get(
            "/api/v1/settings/llm",
            headers={"Authorization": "Bearer server-secret-token"},
        )
        assert response.status_code == 200
        assert response.json() is None
    finally:
        get_settings.cache_clear()


def test_production_fails_closed_when_enabled_bootstrap_token_not_configured(client, monkeypatch):
    try:
        _configure_production(
            monkeypatch,
            token=None,
            bootstrap_enabled=True,
        )
        response = client.get("/api/v1/settings/llm")
        assert response.status_code == 503
        assert response.json()["detail"] == "production authentication is not configured"
    finally:
        get_settings.cache_clear()


def test_development_keeps_legacy_user_header_for_migration(client, monkeypatch):
    try:
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.delenv("AUTH_BEARER_TOKEN", raising=False)
        get_settings.cache_clear()
        response = client.get(
            "/api/v1/settings/llm",
            headers={"X-User-ID": "legacy-test-user"},
        )
        assert response.status_code == 200
        assert response.json() is None
    finally:
        get_settings.cache_clear()


def test_auth_bearer_token_is_redacted_from_logs():
    secret = "server-secret-token"
    redacted = redact_sensitive_text(f"AUTH_BEARER_TOKEN={secret}")
    assert secret not in redacted
    assert "AUTH_BEARER_TOKEN=[REDACTED]" in redacted
