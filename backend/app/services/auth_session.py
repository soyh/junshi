import hashlib
import secrets
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


DEFAULT_SESSION_TTL_SECONDS = 7 * 24 * 60 * 60


class AuthSessionError(ValueError):
    pass


@dataclass(frozen=True)
class CreatedAuthSession:
    access_token: str
    expires_at: str


@dataclass(frozen=True)
class AuthSessionRecord:
    id: str
    user_id: str
    expires_at: str
    created_at: str


class AuthSessionService:
    def __init__(self, *, ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS):
        if ttl_seconds <= 0:
            raise AuthSessionError("session ttl must be positive")
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_now(now: datetime | None) -> datetime:
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        return current_time.astimezone(timezone.utc)

    @staticmethod
    def _parse_expiry(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            expires_at = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at.astimezone(timezone.utc)

    def _active_record_from_row(
        self,
        row: sqlite3.Row | None,
        *,
        now: datetime | None = None,
    ) -> AuthSessionRecord | None:
        if row is None or row["revoked_at"] is not None:
            return None

        expires_at = self._parse_expiry(row["expires_at"])
        if expires_at is None or expires_at <= self._normalize_now(now):
            return None

        return AuthSessionRecord(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            expires_at=str(row["expires_at"]),
            created_at=str(row["created_at"]),
        )

    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        *,
        now: datetime | None = None,
    ) -> CreatedAuthSession:
        user = conn.execute(
            "SELECT 1 FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            raise AuthSessionError("authenticated user does not exist")

        issued_at = self._normalize_now(now)
        expires_at = issued_at + timedelta(seconds=self.ttl_seconds)

        access_token = secrets.token_urlsafe(32)
        conn.execute(
            """
            INSERT INTO auth_sessions (
                id,
                user_id,
                token_hash,
                expires_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                user_id,
                self._token_hash(access_token),
                expires_at.isoformat(),
            ),
        )

        return CreatedAuthSession(
            access_token=access_token,
            expires_at=expires_at.isoformat(),
        )

    def get_active_session(
        self,
        conn: sqlite3.Connection,
        token: str,
        *,
        now: datetime | None = None,
    ) -> AuthSessionRecord | None:
        row = conn.execute(
            """
            SELECT id, user_id, expires_at, revoked_at, created_at
            FROM auth_sessions
            WHERE token_hash = ?
            """,
            (self._token_hash(token),),
        ).fetchone()
        return self._active_record_from_row(row, now=now)

    def resolve(
        self,
        conn: sqlite3.Connection,
        token: str,
        *,
        now: datetime | None = None,
    ) -> str | None:
        session = self.get_active_session(conn, token, now=now)
        return session.user_id if session is not None else None

    def list_active_for_user(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        *,
        now: datetime | None = None,
    ) -> list[AuthSessionRecord]:
        rows = conn.execute(
            """
            SELECT id, user_id, expires_at, revoked_at, created_at
            FROM auth_sessions
            WHERE user_id = ?
              AND revoked_at IS NULL
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()

        result: list[AuthSessionRecord] = []
        for row in rows:
            record = self._active_record_from_row(row, now=now)
            if record is not None:
                result.append(record)
        return result

    def revoke(self, conn: sqlite3.Connection, token: str) -> None:
        conn.execute(
            """
            UPDATE auth_sessions
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE token_hash = ?
              AND revoked_at IS NULL
            """,
            (self._token_hash(token),),
        )

    def revoke_for_user(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        session_id: str,
    ) -> bool:
        cursor = conn.execute(
            """
            UPDATE auth_sessions
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND user_id = ?
              AND revoked_at IS NULL
            """,
            (session_id, user_id),
        )
        return cursor.rowcount == 1

    def revoke_all_for_user(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> int:
        cursor = conn.execute(
            """
            UPDATE auth_sessions
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
              AND revoked_at IS NULL
            """,
            (user_id,),
        )
        return cursor.rowcount

    def revoke_other_sessions(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        current_token: str,
        *,
        now: datetime | None = None,
    ) -> int:
        current_session = self.get_active_session(conn, current_token, now=now)
        if current_session is None or current_session.user_id != user_id:
            raise AuthSessionError("current bearer token is not an active auth session")

        current_time = self._normalize_now(now)
        cursor = conn.execute(
            """
            UPDATE auth_sessions
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
              AND id <> ?
              AND revoked_at IS NULL
              AND expires_at > ?
            """,
            (user_id, current_session.id, current_time.isoformat()),
        )
        return cursor.rowcount

    def rotate(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        current_token: str,
        *,
        now: datetime | None = None,
    ) -> CreatedAuthSession:
        current_session = self.get_active_session(conn, current_token, now=now)
        if current_session is None or current_session.user_id != user_id:
            raise AuthSessionError("current bearer token is not an active auth session")

        self.revoke(conn, current_token)
        return self.create(conn, user_id, now=now)

    def has_active_sessions(
        self,
        conn: sqlite3.Connection,
        *,
        now: datetime | None = None,
    ) -> bool:
        current_time = self._normalize_now(now)
        row = conn.execute(
            """
            SELECT 1
            FROM auth_sessions
            WHERE revoked_at IS NULL
              AND expires_at > ?
            LIMIT 1
            """,
            (current_time.isoformat(),),
        ).fetchone()
        return row is not None
