from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app import backup as backup_cli
from app.core import backup_manifest as manifest_service
from app.core.backup_manifest import (
    BackupManifestError,
    apply_retention,
    create_managed_backup,
    manifest_path_for,
    retention_candidates,
    verify_backup_manifest,
)


def _create_database(path: Path, value: str = "alpha") -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO items (value) VALUES (?)", (value,))


def _managed_backup(
    tmp_path: Path,
    source: Path,
    name: str,
    created_at: datetime,
) -> tuple[Path, Path]:
    return create_managed_backup(source, tmp_path / name, now=created_at)


def test_managed_backup_creates_verifiable_manifest(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "backup.sqlite3"
    _create_database(source)
    created_at = datetime(2026, 9, 18, 6, 30, tzinfo=timezone.utc)

    backup_path, manifest_path = create_managed_backup(source, destination, now=created_at)
    manifest = verify_backup_manifest(manifest_path)

    assert backup_path == destination.resolve()
    assert manifest_path == manifest_path_for(destination)
    assert manifest.schema_version == 1
    assert manifest.created_at == "2026-09-18T06:30:00Z"
    assert manifest.backup_filename == "backup.sqlite3"
    assert manifest.size_bytes == destination.stat().st_size
    assert len(manifest.sha256) == 64
    assert manifest.integrity == "ok"


def test_manifest_verification_rejects_tampered_backup(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "backup.sqlite3"
    _create_database(source)
    _, manifest_path = create_managed_backup(source, destination)

    with destination.open("ab") as target:
        target.write(b"tamper")

    with pytest.raises(BackupManifestError, match="size does not match|checksum does not match"):
        verify_backup_manifest(manifest_path)


def test_manifest_verification_rejects_schema_and_path_tampering(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "backup.sqlite3"
    _create_database(source)
    _, manifest_path = create_managed_backup(source, destination)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["backup_filename"] = "../backup.sqlite3"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(BackupManifestError, match="basename"):
        verify_backup_manifest(manifest_path)

    payload["backup_filename"] = "backup.sqlite3"
    payload["unexpected"] = True
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BackupManifestError, match="fields do not match"):
        verify_backup_manifest(manifest_path)


def test_managed_backup_rolls_back_if_manifest_publish_fails(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "backup.sqlite3"
    _create_database(source)

    def fail_publish(path, payload):
        raise BackupManifestError("forced manifest failure")

    monkeypatch.setattr(manifest_service, "_atomic_write_json", fail_publish)

    with pytest.raises(BackupManifestError, match="forced manifest failure"):
        create_managed_backup(source, destination)

    assert not destination.exists()
    assert not manifest_path_for(destination).exists()


def test_retention_dry_run_selects_only_old_verified_managed_pairs(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    _create_database(source)
    base = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)

    oldest = _managed_backup(tmp_path, source, "backup-1.sqlite3", base)
    middle = _managed_backup(tmp_path, source, "backup-2.sqlite3", base + timedelta(hours=1))
    newest = _managed_backup(tmp_path, source, "backup-3.sqlite3", base + timedelta(hours=2))
    unrelated = tmp_path / "unrelated.sqlite3"
    _create_database(unrelated, "unrelated")

    candidates = retention_candidates(tmp_path, keep=2)
    assert candidates == [oldest]

    dry_run = apply_retention(tmp_path, keep=2, dry_run=True)
    assert dry_run == [oldest]
    assert all(path.exists() for pair in (oldest, middle, newest) for path in pair)
    assert unrelated.exists()


def test_retention_apply_deletes_pairs_but_never_unrelated_files(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    _create_database(source)
    base = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)

    oldest = _managed_backup(tmp_path, source, "backup-1.sqlite3", base)
    middle = _managed_backup(tmp_path, source, "backup-2.sqlite3", base + timedelta(hours=1))
    newest = _managed_backup(tmp_path, source, "backup-3.sqlite3", base + timedelta(hours=2))
    unrelated = tmp_path / "manual-copy.sqlite3"
    _create_database(unrelated, "manual")

    deleted = apply_retention(tmp_path, keep=1, dry_run=False)

    assert deleted == [middle, oldest]
    assert all(not path.exists() for pair in deleted for path in pair)
    assert all(path.exists() for path in newest)
    assert unrelated.exists()
    assert source.exists()


def test_retention_skips_invalid_or_tampered_managed_pairs(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    _create_database(source)
    base = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)

    valid_old = _managed_backup(tmp_path, source, "valid-old.sqlite3", base)
    valid_new = _managed_backup(tmp_path, source, "valid-new.sqlite3", base + timedelta(hours=2))
    tampered = _managed_backup(tmp_path, source, "tampered.sqlite3", base - timedelta(hours=1))
    tampered[0].write_bytes(tampered[0].read_bytes() + b"tamper")

    malformed_manifest = tmp_path / "manual.sqlite3.manifest.json"
    malformed_manifest.write_text("not-json", encoding="utf-8")
    manual = tmp_path / "manual.sqlite3"
    _create_database(manual, "manual")

    candidates = retention_candidates(tmp_path, keep=1)
    assert candidates == [valid_old]
    assert tampered[0].exists() and tampered[1].exists()
    assert manual.exists() and malformed_manifest.exists()
    assert all(path.exists() for path in valid_new)


def test_retention_requires_positive_keep_and_existing_directory(tmp_path: Path):
    with pytest.raises(BackupManifestError, match="at least 1"):
        retention_candidates(tmp_path, keep=0)
    with pytest.raises(BackupManifestError, match="does not exist"):
        retention_candidates(tmp_path / "missing", keep=1)


def test_cli_verify_manifest_and_retention_default_to_dry_run(tmp_path: Path, capsys):
    source = tmp_path / "source.sqlite3"
    _create_database(source)
    base = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)
    old = _managed_backup(tmp_path, source, "old.sqlite3", base)
    _managed_backup(tmp_path, source, "new.sqlite3", base + timedelta(hours=1))

    assert backup_cli.main(["--verify-manifest", str(old[1])]) == 0
    assert "managed backup verified:" in capsys.readouterr().out

    assert backup_cli.main(["--retention-dir", str(tmp_path), "--keep", "1"]) == 0
    output = capsys.readouterr().out
    assert "retention candidate:" in output
    assert old[0].exists() and old[1].exists()
