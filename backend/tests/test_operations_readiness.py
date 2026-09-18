from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app import readiness as readiness_cli
from app.core.backup_manifest import create_managed_backup
from app.core.readiness import ReadinessCheckError, check_readiness


def _migration_dir(tmp_path: Path, versions: tuple[str, ...] = ("001", "002")) -> Path:
    directory = tmp_path / "migrations"
    directory.mkdir()
    for version in versions:
        (directory / f"{version}_migration.sql").write_text("SELECT 1;\n", encoding="utf-8")
    return directory


def _database(path: Path, applied: tuple[str, ...] = ("001", "002")) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.executemany("INSERT INTO schema_migrations(version) VALUES (?)", [(v,) for v in applied])
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO items(value) VALUES ('alpha')")


def _fresh_backup(database: Path, backup_dir: Path, now: datetime, name: str = "app-backup.sqlite3"):
    backup_dir.mkdir(parents=True, exist_ok=True)
    return create_managed_backup(database, backup_dir / name, now=now - timedelta(hours=1))


def test_readiness_passes_for_intact_database_exact_migrations_and_fresh_backup(tmp_path: Path):
    now = datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc)
    database = tmp_path / "app.sqlite3"
    migrations = _migration_dir(tmp_path)
    backup_dir = tmp_path / "backups"
    _database(database)
    _fresh_backup(database, backup_dir, now)

    report = check_readiness(
        database,
        migration_dir=migrations,
        backup_dir=backup_dir,
        max_backup_age_hours=24,
        now=now,
    )

    assert report.ready is True
    assert report.database == {"ok": True, "filename": "app.sqlite3", "error": None}
    assert report.migrations["expected_versions"] == ["001", "002"]
    assert report.migrations["applied_versions"] == ["001", "002"]
    assert report.backup["ok"] is True
    assert report.backup["age_seconds"] == 3600.0


def test_readiness_fails_for_missing_or_unknown_migrations(tmp_path: Path):
    now = datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc)
    migrations = _migration_dir(tmp_path)

    missing = tmp_path / "missing.sqlite3"
    _database(missing, applied=("001",))
    backup_dir = tmp_path / "backups-missing"
    _fresh_backup(missing, backup_dir, now)
    report = check_readiness(missing, migration_dir=migrations, backup_dir=backup_dir, now=now)
    assert report.ready is False
    assert report.migrations["error"] == "applied migrations do not match migration files"

    unknown = tmp_path / "unknown.sqlite3"
    _database(unknown, applied=("001", "002", "999"))
    backup_dir2 = tmp_path / "backups-unknown"
    _fresh_backup(unknown, backup_dir2, now)
    report2 = check_readiness(unknown, migration_dir=migrations, backup_dir=backup_dir2, now=now)
    assert report2.ready is False
    assert report2.migrations["applied_count"] == 3


def test_readiness_fails_closed_for_corrupt_database(tmp_path: Path):
    database = tmp_path / "broken.sqlite3"
    database.write_bytes(b"not-sqlite")
    migrations = _migration_dir(tmp_path)

    report = check_readiness(database, migration_dir=migrations, backup_dir=tmp_path / "backups")

    assert report.ready is False
    assert report.database["ok"] is False
    assert report.database["error"] == "database integrity check failed"
    assert report.migrations["ok"] is False


def test_readiness_requires_a_verified_managed_backup(tmp_path: Path):
    database = tmp_path / "app.sqlite3"
    migrations = _migration_dir(tmp_path)
    _database(database)

    report = check_readiness(database, migration_dir=migrations, backup_dir=tmp_path / "missing-backups")

    assert report.ready is False
    assert report.backup["ok"] is False
    assert report.backup["error"] == "no verified managed backup found"


def test_readiness_rejects_stale_and_future_backups(tmp_path: Path):
    now = datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc)
    database = tmp_path / "app.sqlite3"
    migrations = _migration_dir(tmp_path)
    _database(database)

    stale_dir = tmp_path / "stale"
    stale_dir.mkdir()
    create_managed_backup(database, stale_dir / "stale.sqlite3", now=now - timedelta(hours=25))
    stale = check_readiness(database, migration_dir=migrations, backup_dir=stale_dir, now=now)
    assert stale.ready is False
    assert stale.backup["error"] == "latest verified managed backup is stale"

    future_dir = tmp_path / "future"
    future_dir.mkdir()
    create_managed_backup(database, future_dir / "future.sqlite3", now=now + timedelta(minutes=1))
    future = check_readiness(database, migration_dir=migrations, backup_dir=future_dir, now=now)
    assert future.ready is False
    assert future.backup["error"] == "latest backup timestamp is in the future"


def test_readiness_skips_tampered_backup_and_uses_latest_valid_one(tmp_path: Path):
    now = datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc)
    database = tmp_path / "app.sqlite3"
    migrations = _migration_dir(tmp_path)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    _database(database)

    create_managed_backup(database, backup_dir / "valid.sqlite3", now=now - timedelta(hours=2))
    tampered, _ = create_managed_backup(database, backup_dir / "tampered.sqlite3", now=now - timedelta(hours=1))
    tampered.write_bytes(tampered.read_bytes() + b"tamper")

    report = check_readiness(database, migration_dir=migrations, backup_dir=backup_dir, now=now)

    assert report.ready is True
    assert report.backup["latest_filename"] == "valid.sqlite3"
    assert report.backup["age_seconds"] == 7200.0


def test_readiness_rejects_invalid_age_and_migration_directory(tmp_path: Path):
    database = tmp_path / "app.sqlite3"
    _database(database)

    with pytest.raises(ReadinessCheckError, match="positive"):
        check_readiness(database, migration_dir=tmp_path / "migrations", max_backup_age_hours=0)

    report = check_readiness(database, migration_dir=tmp_path / "missing", backup_dir=tmp_path / "backups")
    assert report.ready is False
    assert report.migrations["error"] == "migration directory does not exist"


def test_duplicate_migration_versions_fail_closed(tmp_path: Path):
    database = tmp_path / "app.sqlite3"
    _database(database, applied=("001",))
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (migrations / "001_second.sql").write_text("SELECT 1;", encoding="utf-8")

    report = check_readiness(database, migration_dir=migrations, backup_dir=tmp_path / "backups")
    assert report.ready is False
    assert report.migrations["error"] == "duplicate migration versions found"


def test_readiness_cli_json_is_machine_readable_and_secret_free(tmp_path: Path, capsys):
    database = tmp_path / "app.sqlite3"
    migrations = _migration_dir(tmp_path)
    backup_dir = tmp_path / "backups"
    _database(database)
    _fresh_backup(database, backup_dir, datetime.now(timezone.utc))

    code = readiness_cli.main(
        [
            "--database",
            str(database),
            "--migrations-dir",
            str(migrations),
            "--backup-dir",
            str(backup_dir),
            "--max-backup-age-hours",
            "24",
            "--json",
        ]
    )
    output = capsys.readouterr().out.strip()
    payload = json.loads(output)

    assert code == 0
    assert payload["ready"] is True
    assert payload["database"]["filename"] == "app.sqlite3"
    assert str(tmp_path) not in output
    assert "authorization" not in output.lower()
    assert "api_key" not in output.lower()
    assert "password" not in output.lower()
