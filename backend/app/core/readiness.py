from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.core.backup import DatabaseBackupError, verify_database
from app.core.backup_manifest import BackupManifestError, MANIFEST_SUFFIX, verify_backup_manifest


class ReadinessCheckError(RuntimeError):
    """Raised when readiness inputs are structurally invalid."""


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    database: dict[str, object]
    migrations: dict[str, object]
    backup: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_migration_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "migrations"


def _readonly_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def _expected_migration_versions(migration_dir: Path) -> list[str]:
    if not migration_dir.is_dir():
        raise ReadinessCheckError("migration directory does not exist")

    versions: list[str] = []
    for path in sorted(migration_dir.glob("*.sql")):
        version = path.name.split("_", 1)[0]
        if not version:
            raise ReadinessCheckError("migration filename has no version")
        versions.append(version)
    if not versions:
        raise ReadinessCheckError("no migration files found")
    if len(set(versions)) != len(versions):
        raise ReadinessCheckError("duplicate migration versions found")
    return versions


def _applied_migration_versions(database_path: Path) -> list[str]:
    try:
        with sqlite3.connect(_readonly_uri(database_path), uri=True, timeout=5.0) as conn:
            rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    except sqlite3.DatabaseError as exc:
        raise ReadinessCheckError("schema_migrations is unavailable") from exc
    return [str(row[0]) for row in rows]


def _parse_created_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReadinessCheckError("backup manifest timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise ReadinessCheckError("backup manifest timestamp lacks timezone")
    return parsed.astimezone(timezone.utc)


def _latest_verified_backup(
    backup_dir: Path,
    *,
    now: datetime,
) -> tuple[str, float] | None:
    if not backup_dir.is_dir():
        return None

    verified: list[tuple[datetime, str]] = []
    for manifest_path in backup_dir.glob(f"*{MANIFEST_SUFFIX}"):
        try:
            manifest = verify_backup_manifest(manifest_path)
            created_at = _parse_created_at(manifest.created_at)
        except (BackupManifestError, ReadinessCheckError):
            continue
        verified.append((created_at, manifest.backup_filename))

    if not verified:
        return None

    created_at, filename = max(verified, key=lambda item: (item[0], item[1]))
    age_seconds = (now - created_at).total_seconds()
    return filename, age_seconds


def check_readiness(
    database_path: str | Path,
    *,
    migration_dir: str | Path | None = None,
    backup_dir: str | Path | None = None,
    max_backup_age_hours: float = 24.0,
    now: datetime | None = None,
) -> ReadinessReport:
    if max_backup_age_hours <= 0:
        raise ReadinessCheckError("max backup age must be positive")

    database = Path(database_path).resolve()
    migrations = Path(migration_dir).resolve() if migration_dir else default_migration_dir().resolve()
    backups = Path(backup_dir).resolve() if backup_dir else database.parent / "backups"
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    current_time = current_time.astimezone(timezone.utc)

    database_ok = True
    database_error: str | None = None
    try:
        verify_database(database)
    except DatabaseBackupError:
        database_ok = False
        database_error = "database integrity check failed"

    expected: list[str] = []
    applied: list[str] = []
    migration_ok = False
    migration_error: str | None = None
    try:
        expected = _expected_migration_versions(migrations)
        if database_ok:
            applied = _applied_migration_versions(database)
            migration_ok = applied == sorted(expected)
            if not migration_ok:
                migration_error = "applied migrations do not match migration files"
        else:
            migration_error = "database integrity failed before migration check"
    except ReadinessCheckError as exc:
        migration_error = str(exc)

    latest = _latest_verified_backup(backups, now=current_time)
    backup_ok = False
    backup_error: str | None = None
    backup_filename: str | None = None
    backup_age_seconds: float | None = None
    if latest is None:
        backup_error = "no verified managed backup found"
    else:
        backup_filename, backup_age_seconds = latest
        max_age_seconds = max_backup_age_hours * 3600.0
        if backup_age_seconds < 0:
            backup_error = "latest backup timestamp is in the future"
        elif backup_age_seconds > max_age_seconds:
            backup_error = "latest verified managed backup is stale"
        else:
            backup_ok = True

    return ReadinessReport(
        ready=database_ok and migration_ok and backup_ok,
        database={
            "ok": database_ok,
            "filename": database.name,
            "error": database_error,
        },
        migrations={
            "ok": migration_ok,
            "expected_count": len(expected),
            "applied_count": len(applied),
            "expected_versions": expected,
            "applied_versions": applied,
            "error": migration_error,
        },
        backup={
            "ok": backup_ok,
            "directory_name": backups.name,
            "latest_filename": backup_filename,
            "age_seconds": backup_age_seconds,
            "max_age_hours": max_backup_age_hours,
            "error": backup_error,
        },
    )
