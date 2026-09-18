from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.readiness import (
    ReadinessCheckError,
    applied_migration_versions,
    default_migration_dir,
    expected_migration_versions,
)


@dataclass(frozen=True)
class RuntimeReadinessReport:
    ready: bool
    database: dict[str, object]
    migrations: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _readonly_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def _database_available(database_path: Path) -> bool:
    if not database_path.is_file():
        return False

    try:
        with sqlite3.connect(_readonly_uri(database_path), uri=True, timeout=2.0) as conn:
            conn.execute("SELECT 1").fetchone()
    except sqlite3.DatabaseError:
        return False
    return True


def check_runtime_readiness(
    database_path: str | Path,
    *,
    migration_dir: str | Path | None = None,
) -> RuntimeReadinessReport:
    """Check only conditions required to safely serve requests right now.

    This intentionally does not inspect managed backups. Backup integrity and
    freshness are operational/release concerns covered by TEST-129/130 and are
    too expensive for a frequently-polled HTTP readiness probe.
    """
    database = Path(database_path).resolve()
    migrations = Path(migration_dir).resolve() if migration_dir else default_migration_dir().resolve()

    database_ok = _database_available(database)
    database_error = None if database_ok else "database unavailable"

    expected_count = 0
    applied_count = 0
    migration_ok = False
    migration_error: str | None = None

    if database_ok:
        try:
            expected = expected_migration_versions(migrations)
            applied = applied_migration_versions(database)
            expected_count = len(expected)
            applied_count = len(applied)
            migration_ok = applied == sorted(expected)
            if not migration_ok:
                migration_error = "applied migrations do not match migration files"
        except ReadinessCheckError as exc:
            migration_error = str(exc)
    else:
        migration_error = "database unavailable before migration check"

    return RuntimeReadinessReport(
        ready=database_ok and migration_ok,
        database={
            "ok": database_ok,
            "error": database_error,
        },
        migrations={
            "ok": migration_ok,
            "expected_count": expected_count,
            "applied_count": applied_count,
            "error": migration_error,
        },
    )
