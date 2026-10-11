import hashlib
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.services.auth_account import normalize_username


DEFAULT_FAILURE_LIMIT = 5
DEFAULT_WINDOW_SECONDS = 15 * 60
DEFAULT_BASE_LOCK_SECONDS = 30
DEFAULT_MAX_LOCK_SECONDS = 15 * 60


@dataclass(frozen=True)
class LoginThrottleState:
    failed_attempts: int
    locked_until: str | None


class AuthLoginThrottleService:
    def __init__(
        self,
        *,
        failure_limit: int = DEFAULT_FAILURE_LIMIT,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        base_lock_seconds: int = DEFAULT_BASE_LOCK_SECONDS,
        max_lock_seconds: int = DEFAULT_MAX_LOCK_SECONDS,
    ):
        if failure_limit <= 0:
            raise ValueError("failure_limit must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if base_lock_seconds <= 0:
            raise ValueError("base_lock_seconds must be positive")
        if max_lock_seconds < base_lock_seconds:
            raise ValueError("max_lock_seconds must be >= base_lock_seconds")

        self.failure_limit = failure_limit
        self.window_seconds = window_seconds
        self.base_lock_seconds = base_lock_seconds
        self.max_lock_seconds = max_lock_seconds

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @classmethod
    def _parse_time(cls, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return cls._as_utc(datetime.fromisoformat(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def subject_hash(username: str) -> str:
        normalized = normalize_username(username)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def retry_after_seconds(
        self,
        conn: sqlite3.Connection,
        username: str,
        *,
        now: datetime | None = None,
    ) -> int | None:
        row = conn.execute(
            """
            SELECT locked_until
            FROM auth_login_throttle
            WHERE subject_hash = ?
            """,
            (self.subject_hash(username),),
        ).fetchone()
        if row is None:
            return None

        current = self._as_utc(now or self._utc_now())
        locked_until = self._parse_time(row["locked_until"])
        if locked_until is None or locked_until <= current:
            return None

        return max(1, math.ceil((locked_until - current).total_seconds()))

    def record_failure(
        self,
        conn: sqlite3.Connection,
        username: str,
        *,
        now: datetime | None = None,
    ) -> LoginThrottleState:
        current = self._as_utc(now or self._utc_now())
        subject_hash = self.subject_hash(username)
        row = conn.execute(
            """
            SELECT failed_attempts, window_started_at
            FROM auth_login_throttle
            WHERE subject_hash = ?
            """,
            (subject_hash,),
        ).fetchone()

        window_started_at = None
        failed_attempts = 0
        if row is not None:
            window_started_at = self._parse_time(row["window_started_at"])
            try:
                failed_attempts = int(row["failed_attempts"])
            except (TypeError, ValueError):
                failed_attempts = 0

        if (
            window_started_at is None
            or current >= window_started_at + timedelta(seconds=self.window_seconds)
        ):
            window_started_at = current
            failed_attempts = 1
        else:
            failed_attempts += 1

        locked_until = None
        if failed_attempts >= self.failure_limit:
            exponent = failed_attempts - self.failure_limit
            lock_seconds = min(
                self.base_lock_seconds * (2**exponent),
                self.max_lock_seconds,
            )
            locked_until = current + timedelta(seconds=lock_seconds)

        conn.execute(
            """
            INSERT INTO auth_login_throttle (
                subject_hash,
                failed_attempts,
                window_started_at,
                locked_until,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(subject_hash) DO UPDATE SET
                failed_attempts = excluded.failed_attempts,
                window_started_at = excluded.window_started_at,
                locked_until = excluded.locked_until,
                updated_at = excluded.updated_at
            """,
            (
                subject_hash,
                failed_attempts,
                window_started_at.isoformat(),
                locked_until.isoformat() if locked_until else None,
                current.isoformat(),
            ),
        )

        return LoginThrottleState(
            failed_attempts=failed_attempts,
            locked_until=locked_until.isoformat() if locked_until else None,
        )

    def clear(self, conn: sqlite3.Connection, username: str) -> None:
        conn.execute(
            "DELETE FROM auth_login_throttle WHERE subject_hash = ?",
            (self.subject_hash(username),),
        )
