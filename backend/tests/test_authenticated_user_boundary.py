import pytest
from fastapi import HTTPException

from app.config.settings import get_settings
from app.core.context import get_current_user_id


LOCAL_USER = "00000000-0000-0000-0000-000000000001"
TOKEN = "test-auth-token-with-sufficient-entropy"


def configure(monkeypatch, *, env="production", token=TOKEN):
    monkeypatch.setenv("APP_ENV", env)
    monkeypatch.setenv("LOCAL_USER_ID", LOCAL_USER)
    if token is None:
        monkeypatch.delenv("AUTH_BEARER_TOKEN", raising=False)
    else:
        monkeypatch.setenv("AUTH_BEARER_TOKEN", token)
    get_settings.cache_clear()


def test_configured_bearer_token_authenticates_fixed_server_side_principal(monkeypatch):
    configure(monkeypatch)

    user_id = get_current_user_id(
        authorization=f"Bearer {TOKEN}",
        x_user_id="attacker-selected-user",
    )

    assert user_id == LOCAL_USER
    assert user_id != "attacker-selected-user"


def test_missing_or_invalid_bearer_token_is_unauthorized(monkeypatch):
    configure(monkeypatch)

    for authorization in (None, "Basic abc", "Bearer wrong-token", "Bearer"):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(authorization=authorization, x_user_id="attacker")
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_production_without_authentication_configuration_fails_closed(monkeypatch):
    configure(monkeypatch, token=None)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(authorization=None, x_user_id="attacker-selected-user")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "authentication is not configured"


def test_development_keeps_legacy_header_only_when_auth_is_unconfigured(monkeypatch):
    configure(monkeypatch, env="development", token=None)

    assert (
        get_current_user_id(authorization=None, x_user_id="legacy-dev-user")
        == "legacy-dev-user"
    )
    assert get_current_user_id(authorization=None, x_user_id=None) == LOCAL_USER


def test_http_routes_require_bearer_when_authentication_is_configured(client, monkeypatch):
    configure(monkeypatch)

    missing = client.get(
        "/api/v1/settings/llm",
        headers={"X-User-ID": "attacker-selected-user"},
    )
    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"

    valid = client.get(
        "/api/v1/settings/llm",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "X-User-ID": "attacker-selected-user",
        },
    )
    assert valid.status_code == 200


def test_health_endpoint_remains_available_without_authentication(client, monkeypatch):
    configure(monkeypatch, token=None)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_provider_settings_ui_uses_bearer_and_never_sends_user_id(client):
    response = client.get("/api/v1/settings/llm/ui")
    assert response.status_code == 200

    body = response.text
    assert 'id="access-token" type="password"' in body
    assert "headers.set('Authorization', `Bearer ${token}`)" in body
    assert 'id="user-id"' not in body
    assert "headers.set('X-User-ID'" not in body
    assert "localStorage" in body  # explanatory text only
    assert "sessionStorage" in body  # explanatory text only
    assert ".innerHTML" not in body

    script = body.split("<script>", 1)[1].split("</script>", 1)[0]
    assert "localStorage." not in script
    assert "sessionStorage." not in script
