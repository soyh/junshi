from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app import restore as restore_cli
from app.core import restore as restore_service
from app.core.restore import DatabaseRestoreError, restore_verified_backup


def _create_database(path: Path, value: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO items (value) VALUES (?)", (value,))


def _read_value(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        return conn.execute("SELECT value FROM items").fetchone()[0]


def test_restore_requires_explicit_offline_confirmation(tmp_path: Path):
    backup = tmp_path / "backup.sqlite3"
    destination = tmp_path / "app.sqlite3"
    _create_database(backup, "backup")
    _create_database(destination, "current")

    with pytest.raises(DatabaseRestoreError, match="offline confirmation"):
        restore_verified_backup(backup, destination)

    assert _read_value(destination) == "current"


def test_corrupt_backup_is_rejected_before_destination_is_touched(tmp_path: Path):
    backup = tmp_path / "broken.sqlite3"
    destination = tmp_path / "app.sqlite3"
    backup.write_bytes(b"broken")
    _create_database(destination, "current")

    with pytest.raises(DatabaseRestoreError, match="backup verification failed"):
        restore_verified_backup(backup, destination, offline_confirmed=True)

    assert _read_value(destination) == "current"


def test_backup_and_destination_must_be_different(tmp_path: Path):
    database = tmp_path / "app.sqlite3"
    _create_database(database, "same")

    with pytest.raises(DatabaseRestoreError, match="different files"):
        restore_verified_backup(database, database, offline_confirmed=True)


def test_restore_atomically_replaces_existing_database(tmp_path: Path):
    backup = tmp_path / "backup.sqlite3"
    destination = tmp_path / "app.sqlite3"
    _create_database(backup, "restored")
    _create_database(destination, "old")

    restored = restore_verified_backup(backup, destination, offline_confirmed=True)

    assert restored == destination.resolve()
    assert _read_value(destination) == "restored"


def test_restore_can_create_missing_destination(tmp_path: Path):
    backup = tmp_path / "backup.sqlite3"
    destination = tmp_path / "nested" / "app.sqlite3"
    _create_database(backup, "restored")

    restore_verified_backup(backup, destination, offline_confirmed=True)

    assert _read_value(destination) == "restored"


def test_restore_removes_stale_wal_and_shm_sidecars(tmp_path: Path):
    backup = tmp_path / "backup.sqlite3"
    destination = tmp_path / "app.sqlite3"
    _create_database(backup, "restored")
    _create_database(destination, "old")
    wal = Path(f"{destination}-wal")
    shm = Path(f"{destination}-shm")
    wal.write_bytes(b"stale-wal")
    shm.write_bytes(b"stale-shm")

    restore_verified_backup(backup, destination, offline_confirmed=True)

    assert not wal.exists()
    assert not shm.exists()
    assert _read_value(destination) == "restored"


def test_failed_candidate_verification_keeps_existing_destination_and_cleans_temp(
    tmp_path: Path,
    monkeypatch,
):
    backup = tmp_path / "backup.sqlite3"
    destination = tmp_path / "app.sqlite3"
    _create_database(backup, "restored")
    _create_database(destination, "current")

    real_verify = restore_service.verify_database
    calls = []

    def verify_then_fail(path):
        calls.append(Path(path).resolve())
        if len(calls) == 1:
            return real_verify(path)
        raise restore_service.DatabaseBackupError("forced candidate failure")

    monkeypatch.setattr(restore_service, "verify_database", verify_then_fail)

    with pytest.raises(DatabaseRestoreError, match="candidate verification failed"):
        restore_verified_backup(backup, destination, offline_confirmed=True)

    assert _read_value(destination) == "current"
    assert list(tmp_path.glob(".*.restore.tmp")) == []


def test_cli_passes_explicit_offline_confirmation_to_restore(tmp_path: Path, monkeypatch, capsys):
    backup = tmp_path / "backup.sqlite3"
    destination = tmp_path / "app.sqlite3"
    _create_database(backup, "backup")
    calls = []

    def fake_restore(backup_path, destination_path, *, offline_confirmed=False):
        calls.append((Path(backup_path).resolve(), Path(destination_path).resolve(), offline_confirmed))
        return Path(destination_path).resolve()

    monkeypatch.setattr(restore_cli, "restore_verified_backup", fake_restore)

    assert restore_cli.main([
        "--backup", str(backup),
        "--destination", str(destination),
        "--offline-confirmed",
    ]) == 0

    assert calls == [(backup.resolve(), destination.resolve(), True)]
    assert "restore complete:" in capsys.readouterr().out
