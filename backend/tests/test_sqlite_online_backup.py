from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app import backup as backup_cli
from app.core import backup as backup_service
from app.core.backup import DatabaseBackupError, create_verified_backup, verify_database


def _create_database(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO items (value) VALUES ('alpha')")


def test_verify_database_accepts_healthy_database(tmp_path: Path):
    database = tmp_path / "healthy.sqlite3"
    _create_database(database)

    verify_database(database)


def test_verify_database_rejects_corrupt_database(tmp_path: Path):
    database = tmp_path / "broken.sqlite3"
    database.write_bytes(b"not-a-sqlite-database")

    with pytest.raises(DatabaseBackupError, match="integrity check failed"):
        verify_database(database)


def test_create_verified_backup_preserves_data(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "backup.sqlite3"
    _create_database(source)

    created = create_verified_backup(source, destination)

    assert created == destination.resolve()
    verify_database(destination)
    with sqlite3.connect(destination) as conn:
        assert conn.execute("SELECT value FROM items").fetchall() == [("alpha",)]


def test_online_backup_includes_committed_wal_data(tmp_path: Path):
    source = tmp_path / "wal.sqlite3"
    destination = tmp_path / "wal-backup.sqlite3"

    writer = sqlite3.connect(source)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        writer.commit()
        writer.execute("INSERT INTO items (value) VALUES ('from-wal')")
        writer.commit()

        create_verified_backup(source, destination)
    finally:
        writer.close()

    with sqlite3.connect(destination) as conn:
        assert conn.execute("SELECT value FROM items").fetchall() == [("from-wal",)]


def test_backup_fails_closed_for_missing_source_and_same_destination(tmp_path: Path):
    missing = tmp_path / "missing.sqlite3"
    destination = tmp_path / "backup.sqlite3"

    with pytest.raises(DatabaseBackupError, match="source database does not exist"):
        create_verified_backup(missing, destination)
    assert not destination.exists()

    source = tmp_path / "source.sqlite3"
    _create_database(source)
    with pytest.raises(DatabaseBackupError, match="must be different"):
        create_verified_backup(source, source)


def test_backup_never_overwrites_existing_destination(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "existing.sqlite3"
    _create_database(source)
    destination.write_bytes(b"keep-me")

    with pytest.raises(DatabaseBackupError, match="destination already exists"):
        create_verified_backup(source, destination)

    assert destination.read_bytes() == b"keep-me"


def test_failed_verification_does_not_publish_partial_backup(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "backup.sqlite3"
    _create_database(source)

    def fail_verification(path):
        raise DatabaseBackupError("forced verification failure")

    monkeypatch.setattr(backup_service, "verify_database", fail_verification)

    with pytest.raises(DatabaseBackupError, match="forced verification failure"):
        create_verified_backup(source, destination)

    assert not destination.exists()
    assert list(tmp_path.glob(".*.tmp")) == []


def test_cli_default_destination_is_timestamped_and_verify_only_uses_same_verifier(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    source = tmp_path / "app.sqlite3"
    _create_database(source)
    fixed_now = datetime(2026, 9, 18, 6, 0, tzinfo=timezone.utc)

    destination = backup_cli.default_backup_destination(source, now=fixed_now)
    assert destination == tmp_path / "backups" / "app-20260918T060000Z.sqlite3"

    called = []

    def fake_verify(path):
        called.append(Path(path).resolve())

    monkeypatch.setattr(backup_cli, "verify_database", fake_verify)
    assert backup_cli.main(["--verify-only", str(source)]) == 0
    assert called == [source.resolve()]
    assert "verified:" in capsys.readouterr().out
