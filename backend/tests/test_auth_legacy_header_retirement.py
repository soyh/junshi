from app.config.settings import get_settings


REGISTER_URL = "/api/v1/auth/register"
PROTECTED_URL = "/api/v1/settings/llm"
PASSWORD = "correct-horse-battery-staple"


def _register(client, username: str) -> str:
    response = client.post(
        REGISTER_URL,
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_development_x_user_id_cannot_select_identity(client, monkeypatch):
    try:
        monkeypatch.setenv("APP_ENV", "development")
        get_settings.cache_clear()

        response = client.get(
            PROTECTED_URL,
            headers={"X-User-ID": "attacker-selected-user"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "X-User-ID is not accepted"}
    finally:
        get_settings.cache_clear()


def test_test_environment_x_user_id_cannot_select_identity(client, monkeypatch):
    try:
        monkeypatch.setenv("APP_ENV", "test")
        get_settings.cache_clear()

        response = client.get(
            PROTECTED_URL,
            headers={"X-User-ID": "attacker-selected-user"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "X-User-ID is not accepted"}
    finally:
        get_settings.cache_clear()


def test_valid_database_session_is_rejected_when_x_user_id_is_also_supplied(client):
    token = _register(client, "header-conflict-user")

    response = client.get(
        PROTECTED_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": "different-user",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "X-User-ID is not accepted"}


def test_development_local_user_fallback_remains_without_legacy_header(client, monkeypatch):
    try:
        monkeypatch.setenv("APP_ENV", "development")
        get_settings.cache_clear()

        response = client.get(PROTECTED_URL)

        assert response.status_code == 200
        assert response.json() is None
    finally:
        get_settings.cache_clear()
