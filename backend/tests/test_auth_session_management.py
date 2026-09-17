from app.config.settings import get_settings


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
SESSIONS_URL = "/api/v1/auth/sessions"
PASSWORD = "correct-horse-battery-staple"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(client, username: str) -> str:
    response = client.post(
        REGISTER_URL,
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _login(client, username: str) -> str:
    response = client.post(
        LOGIN_URL,
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_list_sessions_marks_current_without_exposing_tokens(client):
    first_token = _register(client, "multi-device")
    second_token = _login(client, "multi-device")

    response = client.get(SESSIONS_URL, headers=_auth(second_token))

    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 2
    assert sum(1 for session in sessions if session["current"]) == 1
    for session in sessions:
        assert set(session) == {"id", "expires_at", "created_at", "current"}
        assert first_token not in response.text
        assert second_token not in response.text
        assert "token_hash" not in session


def test_revoke_one_other_session_by_id_preserves_current(client):
    first_token = _register(client, "revoke-one")
    second_token = _login(client, "revoke-one")

    sessions = client.get(SESSIONS_URL, headers=_auth(second_token)).json()
    other_session_id = next(session["id"] for session in sessions if not session["current"])

    revoked = client.delete(
        f"{SESSIONS_URL}/{other_session_id}",
        headers=_auth(second_token),
    )
    assert revoked.status_code == 204

    assert client.get("/api/v1/persons", headers=_auth(first_token)).status_code == 401
    assert client.get("/api/v1/persons", headers=_auth(second_token)).status_code == 200


def test_cross_user_session_id_cannot_be_revoked(client):
    alice_token = _register(client, "session-alice")
    bob_token = _register(client, "session-bob")

    alice_sessions = client.get(SESSIONS_URL, headers=_auth(alice_token)).json()
    alice_session_id = alice_sessions[0]["id"]

    response = client.delete(
        f"{SESSIONS_URL}/{alice_session_id}",
        headers=_auth(bob_token),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "auth session not found"}
    assert client.get("/api/v1/persons", headers=_auth(alice_token)).status_code == 200


def test_revoke_other_sessions_preserves_only_current_session(client):
    first_token = _register(client, "revoke-others")
    second_token = _login(client, "revoke-others")
    current_token = _login(client, "revoke-others")

    response = client.delete(
        f"{SESSIONS_URL}/others",
        headers=_auth(current_token),
    )

    assert response.status_code == 200
    assert response.json() == {"revoked": 2}
    assert client.get("/api/v1/persons", headers=_auth(first_token)).status_code == 401
    assert client.get("/api/v1/persons", headers=_auth(second_token)).status_code == 401
    assert client.get("/api/v1/persons", headers=_auth(current_token)).status_code == 200

    sessions = client.get(SESSIONS_URL, headers=_auth(current_token)).json()
    assert len(sessions) == 1
    assert sessions[0]["current"] is True


def test_rotate_current_session_invalidates_old_token_and_returns_new_session(client):
    old_token = _register(client, "rotate-user")

    response = client.post(
        "/api/v1/auth/session/rotate",
        headers=_auth(old_token),
    )

    assert response.status_code == 200
    new_token = response.json()["access_token"]
    assert new_token
    assert new_token != old_token
    assert client.get("/api/v1/persons", headers=_auth(old_token)).status_code == 401
    assert client.get("/api/v1/persons", headers=_auth(new_token)).status_code == 200

    sessions = client.get(SESSIONS_URL, headers=_auth(new_token)).json()
    assert len(sessions) == 1
    assert sessions[0]["current"] is True


def test_static_bootstrap_token_cannot_rotate_as_database_session(client, monkeypatch):
    try:
        monkeypatch.setenv("AUTH_BEARER_TOKEN", "bootstrap-token")
        monkeypatch.setenv("AUTH_BOOTSTRAP_ENABLED", "true")
        get_settings.cache_clear()

        response = client.post(
            "/api/v1/auth/session/rotate",
            headers=_auth("bootstrap-token"),
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "current bearer token is not an active auth session"
        }
    finally:
        get_settings.cache_clear()


def test_bootstrap_can_be_disabled_without_disabling_account_sessions(client, monkeypatch):
    account_token = _register(client, "bootstrap-retired")

    try:
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("AUTH_BEARER_TOKEN", "retired-bootstrap-token")
        monkeypatch.setenv("AUTH_BOOTSTRAP_ENABLED", "false")
        get_settings.cache_clear()

        retired = client.get(
            "/api/v1/settings/llm",
            headers=_auth("retired-bootstrap-token"),
        )
        assert retired.status_code == 401
        assert retired.json() == {"detail": "invalid bearer token"}

        account_session = client.get(
            "/api/v1/settings/llm",
            headers=_auth(account_token),
        )
        assert account_session.status_code == 200
    finally:
        get_settings.cache_clear()
