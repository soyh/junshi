from datetime import datetime, timedelta, timezone

from app.core.database import get_connection
from app.services.auth_login_throttle import AuthLoginThrottleService


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
PASSWORD = "correct-horse-battery-staple"
WRONG_PASSWORD = "definitely-wrong-password"


def _register(client, username: str = "alice"):
    return client.post(
        REGISTER_URL,
        json={"username": username, "password": PASSWORD},
    )


def _login(client, username: str, password: str):
    return client.post(
        LOGIN_URL,
        json={"username": username, "password": password},
    )


def test_existing_account_is_throttled_after_failure_limit(client):
    assert _register(client).status_code == 201

    for _ in range(5):
        response = _login(client, "alice", WRONG_PASSWORD)
        assert response.status_code == 401
        assert response.json() == {"detail": "invalid credentials"}

    blocked = _login(client, "alice", WRONG_PASSWORD)
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "too many login attempts"}
    assert int(blocked.headers["Retry-After"]) > 0
    assert WRONG_PASSWORD not in blocked.text


def test_unknown_username_has_same_throttle_contract(client):
    for _ in range(5):
        response = _login(client, "missing-user", WRONG_PASSWORD)
        assert response.status_code == 401
        assert response.json() == {"detail": "invalid credentials"}

    blocked = _login(client, "missing-user", WRONG_PASSWORD)
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "too many login attempts"}
    assert int(blocked.headers["Retry-After"]) > 0


def test_successful_login_clears_prior_failures(client):
    assert _register(client).status_code == 201

    for _ in range(4):
        assert _login(client, "alice", WRONG_PASSWORD).status_code == 401

    success = _login(client, "ALICE", PASSWORD)
    assert success.status_code == 200

    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM auth_login_throttle WHERE subject_hash = ?",
            (AuthLoginThrottleService.subject_hash("alice"),),
        ).fetchone()
    assert row is None


def test_throttle_is_scoped_by_normalized_subject(client):
    assert _register(client, "alice").status_code == 201
    assert _register(client, "bob").status_code == 201

    for _ in range(5):
        assert _login(client, "ALICE", WRONG_PASSWORD).status_code == 401

    assert _login(client, "alice", WRONG_PASSWORD).status_code == 429
    assert _login(client, "bob", PASSWORD).status_code == 200


def test_throttle_persists_only_subject_hash_not_raw_unknown_username(client):
    raw_username = "Ghost.User"
    response = _login(client, raw_username, WRONG_PASSWORD)
    assert response.status_code == 401

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT subject_hash, failed_attempts
            FROM auth_login_throttle
            """,
        ).fetchone()

    assert row is not None
    assert row["subject_hash"] == AuthLoginThrottleService.subject_hash(raw_username)
    assert row["subject_hash"] != raw_username.lower()
    assert row["failed_attempts"] == 1


def test_progressive_lock_increases_after_previous_lock_expires(client):
    service = AuthLoginThrottleService(
        failure_limit=2,
        window_seconds=600,
        base_lock_seconds=10,
        max_lock_seconds=40,
    )
    start = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)

    with get_connection() as conn:
        first = service.record_failure(conn, "alice", now=start)
        second = service.record_failure(conn, "alice", now=start + timedelta(seconds=1))

    assert first.failed_attempts == 1
    assert first.locked_until is None
    assert second.failed_attempts == 2
    assert datetime.fromisoformat(second.locked_until) == start + timedelta(seconds=11)

    with get_connection() as conn:
        assert (
            service.retry_after_seconds(
                conn,
                "alice",
                now=start + timedelta(seconds=12),
            )
            is None
        )
        third = service.record_failure(
            conn,
            "alice",
            now=start + timedelta(seconds=12),
        )

    assert third.failed_attempts == 3
    assert datetime.fromisoformat(third.locked_until) == start + timedelta(seconds=32)


def test_failure_window_expiry_resets_counter(client):
    service = AuthLoginThrottleService(
        failure_limit=5,
        window_seconds=60,
        base_lock_seconds=10,
        max_lock_seconds=40,
    )
    start = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)

    with get_connection() as conn:
        for offset in range(4):
            state = service.record_failure(
                conn,
                "alice",
                now=start + timedelta(seconds=offset),
            )
        reset = service.record_failure(
            conn,
            "alice",
            now=start + timedelta(seconds=61),
        )

    assert state.failed_attempts == 4
    assert reset.failed_attempts == 1
    assert reset.locked_until is None


def test_requests_during_lock_do_not_extend_failure_counter(client):
    assert _register(client).status_code == 201

    for _ in range(5):
        assert _login(client, "alice", WRONG_PASSWORD).status_code == 401

    with get_connection() as conn:
        before = conn.execute(
            """
            SELECT failed_attempts, locked_until
            FROM auth_login_throttle
            WHERE subject_hash = ?
            """,
            (AuthLoginThrottleService.subject_hash("alice"),),
        ).fetchone()

    assert _login(client, "alice", WRONG_PASSWORD).status_code == 429

    with get_connection() as conn:
        after = conn.execute(
            """
            SELECT failed_attempts, locked_until
            FROM auth_login_throttle
            WHERE subject_hash = ?
            """,
            (AuthLoginThrottleService.subject_hash("alice"),),
        ).fetchone()

    assert before is not None and after is not None
    assert after["failed_attempts"] == before["failed_attempts"] == 5
    assert after["locked_until"] == before["locked_until"]
