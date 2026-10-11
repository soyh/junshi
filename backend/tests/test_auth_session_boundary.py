import hashlib
from datetime import datetime, timezone

from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.auth_session import AuthSessionService


def _configure_production(
    monkeypatch,
    *,
    bootstrap_token: str | None = None,
    bootstrap_enabled: bool = False,
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


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_authenticated_user_can_exchange_bootstrap_for_opaque_session(client, monkeypatch):
    try:
        _configure_production(
            monkeypatch,
            bootstrap_token="bootstrap-secret",
            bootstrap_enabled=True,
        )

        response = client.post(
            "/api/v1/auth/sessions",
            headers=_bearer("bootstrap-secret"),
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["access_token"] != "bootstrap-secret"

        scoped = client.get(
            "/api/v1/persons",
            headers=_bearer(payload["access_token"]),
        )
        assert scoped.status_code == 200
        assert scoped.json() == []
    finally:
        get_settings.cache_clear()


def test_auth_session_stores_only_token_hash(client, monkeypatch):
    try:
        _configure_production(
            monkeypatch,
            bootstrap_token="bootstrap-secret",
            bootstrap_enabled=True,
        )
        response = client.post(
            "/api/v1/auth/sessions",
            headers=_bearer("bootstrap-secret"),
        )
        token = response.json()["access_token"]

        with get_connection() as conn:
            row = conn.execute(
                "SELECT token_hash FROM auth_sessions"
            ).fetchone()

        assert row is not None
        assert token not in row["token_hash"]
        assert row["token_hash"] == hashlib.sha256(token.encode("utf-8")).hexdigest()
    finally:
        get_settings.cache_clear()


def test_distinct_sessions_resolve_to_distinct_user_scopes(client, monkeypatch):
    try:
        _configure_production(monkeypatch)
        settings = get_settings()
        second_user_id = "00000000-0000-0000-0000-000000000002"
        service = AuthSessionService()

        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id) VALUES (?)",
                (second_user_id,),
            )
            first_session = service.create(conn, settings.local_user_id)
            second_session = service.create(conn, second_user_id)

        first_create = client.post(
            "/api/v1/persons",
            headers=_bearer(first_session.access_token),
            json={"name": "first-user-person"},
        )
        second_create = client.post(
            "/api/v1/persons",
            headers=_bearer(second_session.access_token),
            json={"name": "second-user-person"},
        )
        assert first_create.status_code == 201
        assert second_create.status_code == 201

        first_list = client.get(
            "/api/v1/persons",
            headers=_bearer(first_session.access_token),
        )
        second_list = client.get(
            "/api/v1/persons",
            headers=_bearer(second_session.access_token),
        )

        assert [item["name"] for item in first_list.json()] == ["first-user-person"]
        assert [item["name"] for item in second_list.json()] == ["second-user-person"]
    finally:
        get_settings.cache_clear()


def test_expired_session_is_rejected(client, monkeypatch):
    try:
        _configure_production(monkeypatch)
        settings = get_settings()
        service = AuthSessionService(ttl_seconds=1)

        with get_connection() as conn:
            expired = service.create(
                conn,
                settings.local_user_id,
                now=datetime(2020, 1, 1, tzinfo=timezone.utc),
            )

        response = client.get(
            "/api/v1/persons",
            headers=_bearer(expired.access_token),
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid bearer token"
        assert expired.access_token not in response.text
    finally:
        get_settings.cache_clear()


def test_revoked_session_is_rejected(client, monkeypatch):
    try:
        _configure_production(monkeypatch)
        settings = get_settings()
        service = AuthSessionService()

        with get_connection() as conn:
            created = service.create(conn, settings.local_user_id)
            service.revoke(conn, created.access_token)

        response = client.get(
            "/api/v1/persons",
            headers=_bearer(created.access_token),
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid bearer token"
    finally:
        get_settings.cache_clear()


def test_current_session_can_be_revoked_through_api(client, monkeypatch):
    try:
        _configure_production(
            monkeypatch,
            bootstrap_token="bootstrap-secret",
            bootstrap_enabled=True,
        )
        created = client.post(
            "/api/v1/auth/sessions",
            headers=_bearer("bootstrap-secret"),
        ).json()
        token = created["access_token"]

        revoke = client.delete(
            "/api/v1/auth/session",
            headers=_bearer(token),
        )
        assert revoke.status_code == 204

        rejected = client.get(
            "/api/v1/persons",
            headers=_bearer(token),
        )
        assert rejected.status_code == 401
    finally:
        get_settings.cache_clear()


def test_static_bootstrap_token_is_not_revocable_as_session(client, monkeypatch):
    try:
        _configure_production(
            monkeypatch,
            bootstrap_token="bootstrap-secret",
            bootstrap_enabled=True,
        )
        response = client.delete(
            "/api/v1/auth/session",
            headers=_bearer("bootstrap-secret"),
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "current bearer token is not a revocable auth session"
    finally:
        get_settings.cache_clear()
