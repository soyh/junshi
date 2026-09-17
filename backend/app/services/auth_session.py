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

        issued_at = now or self._utc_now()
        if issued_at.tzinfo is None:
            issued_at = issued_at.replace(tzinfo=timezone.utc)
        issued_at = issued_at.astimezone(timezone.utc)
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

    def resolve(
        self,
        conn: sqlite3.Connection,
        token: str,
        *,
        now: datetime | None = None,
    ) -> str | None:
        row = conn.execute(
            """
            SELECT user_id, expires_at, revoked_at
            FROM auth_sessions
            WHERE token_hash = ?
            """,
            (self._token_hash(token),),
        ).fetchone()
        if row is None or row["revoked_at"] is not None:
            return None

        current_time = now or self._utc_now()
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        current_time = current_time.astimezone(timezone.utc)

        try:
            expires_at = datetime.fromisoformat(row["expires_at"])
        except (TypeError, ValueError):
            return None
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at.astimezone(timezone.utc) <= current_time:
            return None

        return str(row["user_id"])

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

    def has_active_sessions(
        self,
        conn: sqlite3.Connection,
        *,
        now: datetime | None = None,
    ) -> bool:
        current_time = now or self._utc_now()
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        current_time = current_time.astimezone(timezone.utc)
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
