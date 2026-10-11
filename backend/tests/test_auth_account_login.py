from app.core.database import get_connection


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
PASSWORD = "correct-horse-battery-staple"


def _register(client, username: str = "alice", password: str = PASSWORD):
    return client.post(
        REGISTER_URL,
        json={"username": username, "password": password},
    )


def _login(client, username: str = "alice", password: str = PASSWORD):
    return client.post(
        LOGIN_URL,
        json={"username": username, "password": password},
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_server_resolved_user_session(client):
    response = _register(client)

    assert response.status_code == 201
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["expires_at"]

    create_person = client.post(
        "/api/v1/persons",
        headers=_auth(payload["access_token"]),
        json={"name": "Registered User Person"},
    )
    assert create_person.status_code == 201


def test_registration_stores_only_normalized_username_password_hash_and_token_hash(client):
    raw_password = "Never-Store-This-Password-123"
    response = _register(client, username="Alice.User", password=raw_password)
    assert response.status_code == 201
    access_token = response.json()["access_token"]

    with get_connection() as conn:
        credential = conn.execute(
            "SELECT username, password_hash FROM user_credentials",
        ).fetchone()
        session = conn.execute(
            "SELECT token_hash FROM auth_sessions",
        ).fetchone()

    assert credential is not None
    assert credential["username"] == "alice.user"
    assert raw_password not in credential["password_hash"]
    assert credential["password_hash"].startswith("scrypt_v1$")
    assert session is not None
    assert access_token != session["token_hash"]


def test_login_issues_new_session_for_same_user_scope(client):
    registered = _register(client, username="Alice.Mixed")
    assert registered.status_code == 201
    first_token = registered.json()["access_token"]

    created = client.post(
        "/api/v1/persons",
        headers=_auth(first_token),
        json={"name": "Same Scope"},
    )
    assert created.status_code == 201

    logged_in = _login(client, username="ALICE.MIXED")
    assert logged_in.status_code == 200
    second_token = logged_in.json()["access_token"]
    assert second_token != first_token

    persons = client.get(
        "/api/v1/persons",
        headers=_auth(second_token),
    )
    assert persons.status_code == 200
    assert [person["name"] for person in persons.json()] == ["Same Scope"]


def test_wrong_password_and_unknown_username_share_generic_failure(client):
    registered = _register(client)
    assert registered.status_code == 201

    wrong_password = _login(client, password="wrong-password-value")
    unknown_user = _login(client, username="missing-user", password="wrong-password-value")

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json() == {"detail": "invalid credentials"}
    assert unknown_user.json() == {"detail": "invalid credentials"}
    assert "wrong-password-value" not in wrong_password.text
    assert "wrong-password-value" not in unknown_user.text


def test_duplicate_username_is_case_insensitive_after_normalization(client):
    first = _register(client, username="Case.User")
    second = _register(client, username="CASE.USER")

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json() == {"detail": "username unavailable"}

    with get_connection() as conn:
        credential_count = conn.execute(
            "SELECT COUNT(*) AS count FROM user_credentials",
        ).fetchone()["count"]
    assert credential_count == 1


def test_registration_rejects_short_password_before_persistence(client):
    response = _register(client, username="short-pass", password="too-short")

    assert response.status_code == 422
    with get_connection() as conn:
        credential_count = conn.execute(
            "SELECT COUNT(*) AS count FROM user_credentials",
        ).fetchone()["count"]
    assert credential_count == 0


def test_account_credentials_reject_client_selected_user_id(client):
    response = client.post(
        REGISTER_URL,
        json={
            "username": "server-owned-id",
            "password": PASSWORD,
            "user_id": "attacker-selected-user",
        },
    )

    assert response.status_code == 422
    with get_connection() as conn:
        credential_count = conn.execute(
            "SELECT COUNT(*) AS count FROM user_credentials",
        ).fetchone()["count"]
    assert credential_count == 0
