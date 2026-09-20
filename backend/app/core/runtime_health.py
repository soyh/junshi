from __future__ import annotations

import re
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
            # sqlite_master is the long-standing schema table name and is
            # compatible with older SQLite builds used on some production
            # distributions. Reading it forces SQLite to parse the database
            # header/schema, unlike SELECT 1, so corrupt files still fail.
            conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
    except sqlite3.DatabaseError:
        return False
    return True


def _expected_schema_objects(migration_dir: Path) -> set[tuple[str, str]]:
    """Return durable table/index objects declared by repository migrations."""

    table_pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?"
        r"([A-Za-z_][A-Za-z0-9_]*)",
        re.IGNORECASE,
    )
    index_pattern = re.compile(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?"
        r"([A-Za-z_][A-Za-z0-9_]*)",
        re.IGNORECASE,
    )

    objects: set[tuple[str, str]] = set()
    try:
        for path in sorted(migration_dir.glob("*.sql")):
            sql = path.read_text(encoding="utf-8")
            objects.update(("table", name) for name in table_pattern.findall(sql))
            objects.update(("index", name) for name in index_pattern.findall(sql))
    except OSError as exc:
        raise ReadinessCheckError("migration schema declarations are unavailable") from exc

    return objects


def _missing_schema_objects(
    database_path: Path,
    expected_objects: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    if not expected_objects:
        return set()

    try:
        with sqlite3.connect(_readonly_uri(database_path), uri=True, timeout=2.0) as conn:
            rows = conn.execute(
                """
                SELECT type, name
                FROM sqlite_master
                WHERE type IN ('table', 'index')
                """
            ).fetchall()
    except sqlite3.DatabaseError as exc:
        raise ReadinessCheckError("database schema is unavailable") from exc

    actual = {(str(row[0]), str(row[1])) for row in rows}
    return expected_objects - actual


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
            else:
                expected_objects = _expected_schema_objects(migrations)
                if _missing_schema_objects(database, expected_objects):
                    migration_ok = False
                    migration_error = "migration schema objects are missing"
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
