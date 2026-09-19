from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app import portable_backup as portable_cli
from app.config.settings import Settings
from app.core.backup_manifest import create_managed_backup, verify_backup_manifest
from app.core.portable_recovery import (
    PortableRecoveryError,
    apply_portable_retention,
    create_or_reuse_portable_bundle,
    extract_portable_bundle,
    generate_portable_key,
    verify_portable_bundle,
)


def _database(path: Path, value: str = "private relationship evidence") -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO items (value) VALUES (?)", (value,))


def _managed(directory: Path, source: Path, name: str, created_at: datetime):
    directory.mkdir(parents=True, exist_ok=True)
    return create_managed_backup(source, directory / name, now=created_at)


def test_portable_bundle_round_trip_is_encrypted_and_extracts_verified_pair(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    local = tmp_path / "backups"
    exports = tmp_path / "exports"
    extracted = tmp_path / "extracted"
    _database(source)
    backup, _ = _managed(
        local,
        source,
        "app-20260920T010000Z.sqlite3",
        datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc),
    )
    key = generate_portable_key()

    result = create_or_reuse_portable_bundle(local, exports, key=key)
    assert result.reused_existing is False
    bundle = result.report.bundle_path
    assert bundle.name.endswith(".recovery.enc")
    assert bundle.stat().st_mode & 0o777 == 0o600
    raw = bundle.read_bytes()
    assert b"SQLite format 3" not in raw
    assert b"private relationship evidence" not in raw

    report = verify_portable_bundle(bundle, key=key)
    restored_backup, restored_manifest, restored_report = extract_portable_bundle(
        bundle,
        extracted,
        key=key,
    )

    assert restored_report.source_sha256 == report.source_sha256
    assert restored_backup.read_bytes() == backup.read_bytes()
    assert verify_backup_manifest(restored_manifest).sha256 == report.source_sha256
    assert restored_backup.stat().st_mode & 0o777 == 0o600
    assert restored_manifest.stat().st_mode & 0o777 == 0o600


def test_portable_bundle_reuse_is_idempotent_and_wrong_key_or_tamper_fails(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    local = tmp_path / "backups"
    exports = tmp_path / "exports"
    _database(source)
    _managed(local, source, "latest.sqlite3", datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc))
    key = generate_portable_key()

    first = create_or_reuse_portable_bundle(local, exports, key=key)
    second = create_or_reuse_portable_bundle(local, exports, key=key)
    assert first.reused_existing is False
    assert second.reused_existing is True
    assert first.report.bundle_sha256 == second.report.bundle_sha256

    with pytest.raises(PortableRecoveryError, match="verification failed"):
        verify_portable_bundle(first.report.bundle_path, key=generate_portable_key())

    raw = bytearray(first.report.bundle_path.read_bytes())
    raw[len(raw) // 2] ^= 1
    first.report.bundle_path.write_bytes(raw)
    with pytest.raises(PortableRecoveryError, match="verification failed"):
        verify_portable_bundle(first.report.bundle_path, key=key)


def test_portable_retention_only_deletes_verified_portable_bundles(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    local = tmp_path / "backups"
    exports = tmp_path / "exports"
    _database(source)
    key = generate_portable_key()
    base = datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc)
    bundles = []

    for index in range(3):
        _managed(local, source, f"backup-{index}.sqlite3", base + timedelta(hours=index))
        result = create_or_reuse_portable_bundle(local, exports, key=key)
        bundles.append(result.report.bundle_path)

    invalid = exports / "invalid.recovery.enc"
    invalid.write_bytes(b"not-valid")
    unrelated = exports / "keep.txt"
    unrelated.write_text("keep", encoding="utf-8")

    candidates = apply_portable_retention(exports, key=key, keep=1, dry_run=True)
    assert candidates == [bundles[1], bundles[0]]
    deleted = apply_portable_retention(exports, key=key, keep=1, dry_run=False)
    assert deleted == candidates
    assert bundles[2].exists()
    assert invalid.exists() and unrelated.exists()


def test_extract_refuses_overwrite(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    local = tmp_path / "backups"
    exports = tmp_path / "exports"
    extracted = tmp_path / "extracted"
    _database(source)
    _managed(local, source, "latest.sqlite3", datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc))
    key = generate_portable_key()
    bundle = create_or_reuse_portable_bundle(local, exports, key=key).report.bundle_path

    extract_portable_bundle(bundle, extracted, key=key)
    with pytest.raises(PortableRecoveryError, match="already exists"):
        extract_portable_bundle(bundle, extracted, key=key)


def test_cli_check_prepare_verify_and_extract(tmp_path: Path, monkeypatch, capsys):
    source = tmp_path / "app.sqlite3"
    local = tmp_path / "backups"
    exports = tmp_path / "exports"
    extracted = tmp_path / "extracted"
    _database(source)
    key = generate_portable_key()

    monkeypatch.setattr(
        portable_cli,
        "get_settings",
        lambda: Settings(
            database_path=str(source),
            portable_backup_directory=str(exports),
            portable_backup_encryption_key=key,
            portable_backup_keep=7,
        ),
    )

    assert portable_cli.main(["--check", "--local-dir", str(local), "--json"]) == 0
    assert '"ok": true' in capsys.readouterr().out

    assert portable_cli.main(["--prepare", "--local-dir", str(local), "--json"]) == 0
    prepared = capsys.readouterr().out
    assert '"bundle_sha256"' in prepared

    bundle = next(exports.glob("*.recovery.enc"))
    assert portable_cli.main(["--verify", str(bundle), "--json"]) == 0
    assert '"ok": true' in capsys.readouterr().out

    assert portable_cli.main([
        "--extract", str(bundle),
        "--destination-dir", str(extracted),
        "--json",
    ]) == 0
    assert '"manifest"' in capsys.readouterr().out


def test_cli_fails_closed_without_encryption_key(tmp_path: Path, monkeypatch, capsys):
    source = tmp_path / "app.sqlite3"
    _database(source)
    monkeypatch.setattr(
        portable_cli,
        "get_settings",
        lambda: Settings(
            database_path=str(source),
            portable_backup_directory=str(tmp_path / "exports"),
            portable_backup_encryption_key=None,
        ),
    )
    assert portable_cli.main(["--check", "--json"]) == 1
    assert "not configured" in capsys.readouterr().out


def test_windows_pull_script_uses_ssh_scp_sha256_and_dpapi_without_plain_env_snapshot():
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts/windows/backup-pull.ps1").read_text(encoding="utf-8")

    assert "app.portable_backup --prepare --json" in script
    assert "Get-FileHash -Algorithm SHA256" in script
    assert "ConvertFrom-SecureString" in script
    assert "production.env.dpapi" in script
    assert "Remove-Item -Force -LiteralPath $EnvTemp" in script
    assert "repository = \"soyh/junshi\"" in script
    assert "8899" not in script


def test_windows_restore_script_is_stage_only_by_default_and_apply_is_explicit():
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts/windows/restore-push.ps1").read_text(encoding="utf-8")

    assert "[switch]$ApplyRestore" in script
    assert "if (-not $ApplyRestore)" in script
    assert "RESTORE_PUSH=STAGED" in script
    assert "app.portable_backup --extract" in script
    assert "app.backup --verify-manifest" in script
    assert "app.restore --backup" in script
    assert "--offline-confirmed" in script
    assert "systemctl stop" in script
    assert "app.probe live --json" in script
    assert "app.probe ready --json" in script
    assert "app.preflight --json" in script
    assert "8899" not in script
    assert script.index("if (-not $ApplyRestore)") < script.index("systemctl stop")
