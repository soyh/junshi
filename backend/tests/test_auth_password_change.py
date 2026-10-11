from app.config.settings import get_settings
from app.core.database import get_connection


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
PASSWORD_URL = "/api/v1/auth/password"
OLD_PASSWORD = "correct-horse-battery-staple"
NEW_PASSWORD = "new-correct-horse-battery-staple"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(client, username: str, password: str = OLD_PASSWORD):
    return client.post(
        REGISTER_URL,
        json={"username": username, "password": password},
    )


def _login(client, username: str, password: str):
    return client.post(
        LOGIN_URL,
        json={"username": username, "password": password},
    )


def _change_password(client, token: str, current: str, new: str = NEW_PASSWORD):
    return client.put(
        PASSWORD_URL,
        headers=_auth(token),
        json={"current_password": current, "new_password": new},
    )


def test_password_change_requires_authentication(client):
    response = client.put(
        PASSWORD_URL,
        json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 401


def test_password_change_rotates_credentials_and_current_session(client):
    registered = _register(client, "alice")
    assert registered.status_code == 201
    old_token = registered.json()["access_token"]

    changed = _change_password(client, old_token, OLD_PASSWORD)
    assert changed.status_code == 200
    new_token = changed.json()["access_token"]
    assert new_token
    assert new_token != old_token

    old_session = client.get("/api/v1/persons", headers=_auth(old_token))
    new_session = client.get("/api/v1/persons", headers=_auth(new_token))
    assert old_session.status_code == 401
    assert new_session.status_code == 200

    old_login = _login(client, "alice", OLD_PASSWORD)
    new_login = _login(client, "alice", NEW_PASSWORD)
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_password_change_revokes_all_existing_sessions_for_user(client):
    registered = _register(client, "alice")
    assert registered.status_code == 201
    first_token = registered.json()["access_token"]

    second_login = _login(client, "alice", OLD_PASSWORD)
    assert second_login.status_code == 200
    second_token = second_login.json()["access_token"]

    changed = _change_password(client, second_token, OLD_PASSWORD)
    assert changed.status_code == 200
    replacement_token = changed.json()["access_token"]

    assert client.get("/api/v1/persons", headers=_auth(first_token)).status_code == 401
    assert client.get("/api/v1/persons", headers=_auth(second_token)).status_code == 401
    assert client.get("/api/v1/persons", headers=_auth(replacement_token)).status_code == 200


def test_wrong_current_password_is_atomic_and_preserves_existing_session(client):
    registered = _register(client, "alice")
    assert registered.status_code == 201
    token = registered.json()["access_token"]

    with get_connection() as conn:
        before_hash = conn.execute(
            "SELECT password_hash FROM user_credentials WHERE username = ?",
            ("alice",),
        ).fetchone()["password_hash"]

    changed = _change_password(client, token, "wrong-current-password")
    assert changed.status_code == 401
    assert changed.json() == {"detail": "invalid current password"}
    assert "wrong-current-password" not in changed.text

    with get_connection() as conn:
        after_hash = conn.execute(
            "SELECT password_hash FROM user_credentials WHERE username = ?",
            ("alice",),
        ).fetchone()["password_hash"]

    assert after_hash == before_hash
    assert client.get("/api/v1/persons", headers=_auth(token)).status_code == 200
    assert _login(client, "alice", OLD_PASSWORD).status_code == 200


def test_password_change_does_not_revoke_other_user_sessions(client):
    alice = _register(client, "alice")
    bob = _register(client, "bob-user")
    assert alice.status_code == 201
    assert bob.status_code == 201

    alice_token = alice.json()["access_token"]
    bob_token = bob.json()["access_token"]

    changed = _change_password(client, alice_token, OLD_PASSWORD)
    assert changed.status_code == 200

    bob_scope = client.get("/api/v1/persons", headers=_auth(bob_token))
    assert bob_scope.status_code == 200


def test_password_change_stores_only_new_scrypt_hash(client):
    registered = _register(client, "alice")
    assert registered.status_code == 201
    token = registered.json()["access_token"]

    changed = _change_password(client, token, OLD_PASSWORD)
    assert changed.status_code == 200

    with get_connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM user_credentials WHERE username = ?",
            ("alice",),
        ).fetchone()

    assert row is not None
    password_hash = str(row["password_hash"])
    assert password_hash.startswith("scrypt_v1$")
    assert OLD_PASSWORD not in password_hash
    assert NEW_PASSWORD not in password_hash


def test_password_change_rejects_client_selected_user_id(client):
    registered = _register(client, "alice")
    assert registered.status_code == 201
    token = registered.json()["access_token"]

    response = client.put(
        PASSWORD_URL,
        headers=_auth(token),
        json={
            "current_password": OLD_PASSWORD,
            "new_password": NEW_PASSWORD,
            "user_id": "attacker-selected-user",
        },
    )

    assert response.status_code == 422
    assert client.get("/api/v1/persons", headers=_auth(token)).status_code == 200


def test_static_bootstrap_token_cannot_change_password(client, monkeypatch):
    try:
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("AUTH_BEARER_TOKEN", "server-secret-token")
        monkeypatch.setenv("AUTH_BOOTSTRAP_ENABLED", "true")
        get_settings.cache_clear()

        response = client.put(
            PASSWORD_URL,
            headers=_auth("server-secret-token"),
            json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
        )

        assert response.status_code == 403
        assert response.json() == {
            "detail": "password change requires an active account session"
        }
        assert "server-secret-token" not in response.text
    finally:
        get_settings.cache_clear()
