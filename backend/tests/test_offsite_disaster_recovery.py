from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app import offsite_backup as offsite_cli
from app.config import settings as settings_module
from app.config.settings import Settings
from app.core.backup_manifest import create_managed_backup
from app.core.offsite_backup import (
    OffsiteBackupError,
    apply_offsite_retention,
    create_encrypted_offsite_bundle,
    decode_offsite_key,
    export_latest_managed_backup,
    generate_offsite_key,
    latest_verified_managed_backup,
    require_separate_storage,
    verify_offsite_bundle,
)


def _database(path: Path, value: str = "private relationship evidence") -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO items (value) VALUES (?)", (value,))


def _managed(
    directory: Path,
    source: Path,
    name: str,
    created_at: datetime,
):
    return create_managed_backup(source, directory / name, now=created_at)


def test_generated_key_is_32_bytes_and_invalid_keys_fail():
    key = generate_offsite_key()
    assert len(decode_offsite_key(key)) == 32

    with pytest.raises(OffsiteBackupError, match="not configured"):
        decode_offsite_key(None)
    with pytest.raises(OffsiteBackupError, match="32 bytes"):
        decode_offsite_key("YQ==")


def test_encrypted_bundle_round_trip_reuses_managed_manifest_and_hides_plaintext(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    local = tmp_path / "local"
    remote = tmp_path / "remote"
    local.mkdir()
    remote.mkdir()
    _database(source)
    created = datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc)
    backup, manifest = _managed(local, source, "app-20260920T010000Z.sqlite3", created)
    key = generate_offsite_key()
    bundle = remote / f"{backup.name}.offsite.enc"

    created_report = create_encrypted_offsite_bundle(backup, manifest, bundle, key=key)
    verified_report = verify_offsite_bundle(bundle, key=key)

    assert created_report == verified_report
    assert verified_report.source_backup_filename == backup.name
    assert verified_report.source_created_at == "2026-09-20T01:00:00Z"
    assert verified_report.source_size_bytes == backup.stat().st_size
    assert bundle.stat().st_mode & 0o777 == 0o600
    ciphertext = bundle.read_bytes()
    assert b"SQLite format 3" not in ciphertext
    assert b"private relationship evidence" not in ciphertext


def test_offsite_bundle_rejects_wrong_key_and_ciphertext_tampering(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    local = tmp_path / "local"
    remote = tmp_path / "remote"
    local.mkdir()
    remote.mkdir()
    _database(source)
    backup, manifest = _managed(
        local,
        source,
        "app.sqlite3",
        datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc),
    )
    key = generate_offsite_key()
    bundle = remote / "app.sqlite3.offsite.enc"
    create_encrypted_offsite_bundle(backup, manifest, bundle, key=key)

    with pytest.raises(OffsiteBackupError, match="authentication failed"):
        verify_offsite_bundle(bundle, key=generate_offsite_key())

    raw = bytearray(bundle.read_bytes())
    raw[len(raw) // 2] ^= 0x01
    bundle.write_bytes(raw)
    with pytest.raises(OffsiteBackupError, match="authentication failed"):
        verify_offsite_bundle(bundle, key=key)


def test_latest_verified_backup_skips_tampered_pair(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    local = tmp_path / "local"
    local.mkdir()
    _database(source)
    base = datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc)
    old = _managed(local, source, "old.sqlite3", base)
    newest = _managed(local, source, "new.sqlite3", base + timedelta(hours=1))
    newest[0].write_bytes(newest[0].read_bytes() + b"tamper")

    backup, manifest = latest_verified_managed_backup(local)
    assert (backup, manifest) == old


def test_same_storage_destination_is_rejected(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    remote = tmp_path / "remote"
    remote.mkdir()
    _database(source)

    with pytest.raises(OffsiteBackupError, match="storage separate"):
        require_separate_storage(source, remote)


def test_export_can_be_exercised_without_storage_gate_but_default_gate_is_strict(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    local = tmp_path / "local"
    remote = tmp_path / "remote"
    local.mkdir()
    remote.mkdir()
    _database(source)
    _managed(local, source, "latest.sqlite3", datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc))
    key = generate_offsite_key()

    with pytest.raises(OffsiteBackupError, match="storage separate"):
        export_latest_managed_backup(local, remote, key=key)

    report = export_latest_managed_backup(
        local,
        remote,
        key=key,
        require_distinct_storage=False,
    )
    assert report.bundle_path.exists()
    assert verify_offsite_bundle(report.bundle_path, key=key).source_sha256 == report.source_sha256


def test_offsite_retention_deletes_only_verified_encrypted_bundles(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    local = tmp_path / "local"
    remote = tmp_path / "remote"
    local.mkdir()
    remote.mkdir()
    _database(source)
    key = generate_offsite_key()
    base = datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc)
    bundles = []

    for index in range(3):
        backup, manifest = _managed(
            local,
            source,
            f"backup-{index}.sqlite3",
            base + timedelta(hours=index),
        )
        bundle = remote / f"{backup.name}.offsite.enc"
        create_encrypted_offsite_bundle(backup, manifest, bundle, key=key)
        bundles.append(bundle)

    unrelated = remote / "do-not-delete.txt"
    unrelated.write_text("keep", encoding="utf-8")
    invalid = remote / "invalid.offsite.enc"
    invalid.write_bytes(b"not-a-valid-bundle")

    candidates = apply_offsite_retention(remote, key=key, keep=1, dry_run=True)
    assert candidates == [bundles[1], bundles[0]]
    assert all(path.exists() for path in bundles)

    deleted = apply_offsite_retention(remote, key=key, keep=1, dry_run=False)
    assert deleted == candidates
    assert bundles[2].exists()
    assert not bundles[1].exists() and not bundles[0].exists()
    assert unrelated.exists() and invalid.exists()


def test_cli_check_is_fail_closed_until_destination_is_distinct_storage(tmp_path: Path, monkeypatch, capsys):
    source = tmp_path / "app.sqlite3"
    local = tmp_path / "backups"
    remote = tmp_path / "remote"
    local.mkdir()
    remote.mkdir()
    _database(source)
    _managed(local, source, "latest.sqlite3", datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc))
    key = generate_offsite_key()

    settings_module.get_settings.cache_clear()
    monkeypatch.setattr(
        offsite_cli,
        "get_settings",
        lambda: Settings(
            database_path=str(source),
            offsite_backup_directory=str(remote),
            offsite_backup_encryption_key=key,
            offsite_backup_keep=30,
        ),
    )

    assert offsite_cli.main(["--check", "--json"]) == 1
    assert "storage separate" in capsys.readouterr().out

    monkeypatch.setattr(offsite_cli, "require_separate_storage", lambda source, destination: None)
    assert offsite_cli.main(["--check", "--json"]) == 0
    output = capsys.readouterr().out
    assert '"ok": true' in output
    assert '"separate_storage": true' in output


def test_systemd_offsite_contract_is_explicit_and_does_not_restart_runtime():
    root = Path(__file__).resolve().parents[2]
    service = (root / "deploy/systemd/ai-love-strategist-offsite-backup.service").read_text(encoding="utf-8")
    timer = (root / "deploy/systemd/ai-love-strategist-offsite-backup.timer").read_text(encoding="utf-8")
    installer = (root / "deploy/systemd/install-offsite-backup.sh").read_text(encoding="utf-8")

    assert "python -m app.offsite_backup --json --apply-retention" in service
    assert "After=network-online.target ai-love-strategist-backup.service" in service
    assert "Persistent=true" in timer
    assert "RandomizedDelaySec=15m" in timer
    assert "python -m app.offsite_backup --check --json" in installer
    assert installer.index("python -m app.offsite_backup --check --json") < installer.index("install -m 0644")
    assert "systemctl enable \"$TIMER\"" in installer
    assert "systemctl start ai-love-strategist.service" not in installer
    assert "systemctl restart ai-love-strategist.service" not in installer
    assert "8899" not in service + timer + installer
