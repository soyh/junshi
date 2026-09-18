from pathlib import Path

from app.config.settings import Settings, get_settings


PROTECTED_URL = "/api/v1/settings/llm"
REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
PASSWORD = "correct-horse-battery-staple"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _configure_production(
    monkeypatch,
    *,
    bootstrap_enabled: bool,
    bootstrap_token: str | None = None,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "AUTH_BOOTSTRAP_ENABLED",
        "true" if bootstrap_enabled else "false",
    )
    if bootstrap_token is None:
        monkeypatch.delenv("AUTH_BEARER_TOKEN", raising=False)
    else:
        monkeypatch.setenv("AUTH_BEARER_TOKEN", bootstrap_token)
    get_settings.cache_clear()


def test_bootstrap_setting_defaults_disabled():
    assert Settings.model_fields["auth_bootstrap_enabled"].default is False


def test_env_example_disables_bootstrap_by_default():
    env_example = (REPOSITORY_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "AUTH_BOOTSTRAP_ENABLED=false" in env_example
    assert "AUTH_BOOTSTRAP_ENABLED=true" not in env_example


def test_production_rejects_static_token_when_bootstrap_is_disabled(client, monkeypatch):
    try:
        _configure_production(
            monkeypatch,
            bootstrap_enabled=False,
            bootstrap_token="retired-bootstrap-token",
        )

        response = client.get(
            PROTECTED_URL,
            headers=_auth("retired-bootstrap-token"),
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "invalid bearer token"}
        assert "retired-bootstrap-token" not in response.text
    finally:
        get_settings.cache_clear()


def test_production_can_explicitly_opt_in_to_transitional_bootstrap(client, monkeypatch):
    try:
        _configure_production(
            monkeypatch,
            bootstrap_enabled=True,
            bootstrap_token="migration-bootstrap-token",
        )

        response = client.get(
            PROTECTED_URL,
            headers=_auth("migration-bootstrap-token"),
        )

        assert response.status_code == 200
        assert response.json() is None
    finally:
        get_settings.cache_clear()


def test_account_login_session_works_with_bootstrap_disabled(client, monkeypatch):
    try:
        _configure_production(monkeypatch, bootstrap_enabled=False)

        registered = client.post(
            REGISTER_URL,
            json={"username": "bootstrap-retired-account", "password": PASSWORD},
        )
        assert registered.status_code == 201
        registered_token = registered.json()["access_token"]
        assert client.get(PROTECTED_URL, headers=_auth(registered_token)).status_code == 200

        logged_in = client.post(
            LOGIN_URL,
            json={"username": "bootstrap-retired-account", "password": PASSWORD},
        )
        assert logged_in.status_code == 200
        login_token = logged_in.json()["access_token"]
        assert login_token != registered_token
        assert client.get(PROTECTED_URL, headers=_auth(login_token)).status_code == 200
    finally:
        get_settings.cache_clear()


def test_production_without_bootstrap_or_session_requires_bearer(client, monkeypatch):
    try:
        _configure_production(monkeypatch, bootstrap_enabled=False)

        response = client.get(PROTECTED_URL)

        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
        assert response.json() == {"detail": "bearer token required"}
    finally:
        get_settings.cache_clear()