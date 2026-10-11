from __future__ import annotations

import json
import os
import struct
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.core.backup_manifest import MANIFEST_SUFFIX, BackupManifestError, verify_backup_manifest
from app.core.offsite_backup import (
    MAX_MANIFEST_BYTES,
    OffsiteBackupError,
    OffsiteBundleReport,
    _decrypt_bundle_to_payload,
    create_encrypted_offsite_bundle,
    decode_offsite_key,
    generate_offsite_key,
    latest_verified_managed_backup,
    verify_offsite_bundle,
)


PORTABLE_SUFFIX = ".recovery.enc"
PORTABLE_CHUNK_BYTES = 1024 * 1024


class PortableRecoveryError(RuntimeError):
    """Raised when a portable recovery bundle cannot be created or restored safely."""


@dataclass(frozen=True)
class PortableBundleResult:
    report: OffsiteBundleReport
    reused_existing: bool


def generate_portable_key() -> str:
    return generate_offsite_key()


def validate_portable_key(value: str | None) -> str:
    try:
        decode_offsite_key(value)
    except OffsiteBackupError as exc:
        raise PortableRecoveryError(str(exc)) from exc
    assert value is not None
    return value


def ensure_private_directory(directory: str | Path) -> Path:
    path = Path(directory).resolve()
    try:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path, 0o700)
    except OSError as exc:
        raise PortableRecoveryError(f"cannot prepare recovery directory: {path}") from exc
    if not path.is_dir():
        raise PortableRecoveryError(f"recovery path is not a directory: {path}")
    return path


def _report_created_at(report: OffsiteBundleReport) -> datetime:
    try:
        value = datetime.fromisoformat(report.source_created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PortableRecoveryError("portable bundle created_at is invalid") from exc
    if value.tzinfo is None:
        raise PortableRecoveryError("portable bundle created_at must include timezone")
    return value


def create_or_reuse_portable_bundle(
    local_backup_directory: str | Path,
    export_directory: str | Path,
    *,
    key: str,
) -> PortableBundleResult:
    validate_portable_key(key)
    local_dir = Path(local_backup_directory).resolve()
    export_dir = ensure_private_directory(export_directory)

    try:
        backup_path, manifest_path = latest_verified_managed_backup(local_dir)
        managed = verify_backup_manifest(manifest_path)
    except (OffsiteBackupError, BackupManifestError) as exc:
        raise PortableRecoveryError("no usable verified managed backup is available") from exc

    destination = export_dir / f"{backup_path.name}{PORTABLE_SUFFIX}"
    if destination.exists():
        try:
            report = verify_offsite_bundle(destination, key=key)
        except OffsiteBackupError as exc:
            raise PortableRecoveryError("existing portable recovery bundle is invalid") from exc
        if (
            report.source_backup_filename != managed.backup_filename
            or report.source_sha256 != managed.sha256
            or report.source_size_bytes != managed.size_bytes
        ):
            raise PortableRecoveryError(
                "existing portable recovery bundle does not match the latest managed backup"
            )
        return PortableBundleResult(report=report, reused_existing=True)

    try:
        report = create_encrypted_offsite_bundle(
            backup_path,
            manifest_path,
            destination,
            key=key,
        )
    except OffsiteBackupError as exc:
        raise PortableRecoveryError("portable recovery bundle creation failed") from exc
    return PortableBundleResult(report=report, reused_existing=False)


def verify_portable_bundle(bundle: str | Path, *, key: str) -> OffsiteBundleReport:
    validate_portable_key(key)
    try:
        return verify_offsite_bundle(bundle, key=key)
    except OffsiteBackupError as exc:
        raise PortableRecoveryError("portable recovery bundle verification failed") from exc


def _parse_payload_manifest(payload, destination: Path) -> tuple[bytes, str]:
    length_raw = payload.read(8)
    if len(length_raw) != 8:
        raise PortableRecoveryError("portable recovery payload header is truncated")
    manifest_length = struct.unpack(">Q", length_raw)[0]
    if manifest_length < 1 or manifest_length > MAX_MANIFEST_BYTES:
        raise PortableRecoveryError("portable recovery manifest length is invalid")
    manifest_bytes = payload.read(manifest_length)
    if len(manifest_bytes) != manifest_length:
        raise PortableRecoveryError("portable recovery manifest is truncated")
    try:
        raw_manifest = json.loads(manifest_bytes.decode("utf-8"))
        backup_filename = str(raw_manifest["backup_filename"])
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise PortableRecoveryError("portable recovery manifest payload is invalid") from exc
    if Path(backup_filename).name != backup_filename:
        raise PortableRecoveryError("portable recovery backup filename is unsafe")
    if destination / backup_filename == destination:
        raise PortableRecoveryError("portable recovery backup filename is invalid")
    return manifest_bytes, backup_filename


def extract_portable_bundle(
    bundle: str | Path,
    destination_directory: str | Path,
    *,
    key: str,
) -> tuple[Path, Path, OffsiteBundleReport]:
    report = verify_portable_bundle(bundle, key=key)
    destination = ensure_private_directory(destination_directory)
    encryption_key = decode_offsite_key(key)

    with tempfile.TemporaryDirectory(prefix="als-portable-recovery-") as temp_raw:
        temp_dir = Path(temp_raw)
        payload_path = temp_dir / "payload.bin"
        try:
            _decrypt_bundle_to_payload(Path(bundle).resolve(), payload_path, encryption_key)
        except OffsiteBackupError as exc:
            raise PortableRecoveryError("portable recovery bundle decryption failed") from exc

        with payload_path.open("rb") as payload:
            manifest_bytes, backup_filename = _parse_payload_manifest(payload, destination)
            backup_path = destination / backup_filename
            manifest_path = destination / f"{backup_filename}{MANIFEST_SUFFIX}"
            if backup_path.exists() or manifest_path.exists():
                raise PortableRecoveryError("portable recovery extraction destination already exists")

            temp_backup = destination / f".{backup_filename}.{uuid.uuid4().hex}.tmp"
            temp_manifest = destination / f".{backup_filename}.{uuid.uuid4().hex}.manifest.tmp"
            try:
                with temp_backup.open("xb") as target:
                    for chunk in iter(lambda: payload.read(PORTABLE_CHUNK_BYTES), b""):
                        target.write(chunk)
                    target.flush()
                    os.fsync(target.fileno())
                temp_manifest.write_bytes(manifest_bytes)
                os.chmod(temp_backup, 0o600)
                os.chmod(temp_manifest, 0o600)
                os.replace(temp_backup, backup_path)
                os.replace(temp_manifest, manifest_path)
            except OSError as exc:
                temp_backup.unlink(missing_ok=True)
                temp_manifest.unlink(missing_ok=True)
                backup_path.unlink(missing_ok=True)
                manifest_path.unlink(missing_ok=True)
                raise PortableRecoveryError("portable recovery extraction publish failed") from exc

    try:
        managed = verify_backup_manifest(manifest_path)
    except BackupManifestError as exc:
        backup_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise PortableRecoveryError("extracted managed backup verification failed") from exc

    if managed.sha256 != report.source_sha256:
        backup_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise PortableRecoveryError("extracted backup does not match portable bundle metadata")

    return backup_path, manifest_path, report


def verified_portable_bundles(directory: str | Path, *, key: str) -> list[OffsiteBundleReport]:
    validate_portable_key(key)
    path = Path(directory).resolve()
    if not path.is_dir():
        raise PortableRecoveryError(f"portable recovery directory does not exist: {path}")
    reports: list[OffsiteBundleReport] = []
    for bundle in path.glob(f"*{PORTABLE_SUFFIX}"):
        try:
            reports.append(verify_portable_bundle(bundle, key=key))
        except PortableRecoveryError:
            continue
    reports.sort(key=lambda item: (_report_created_at(item), item.bundle_path.name), reverse=True)
    return reports


def apply_portable_retention(
    directory: str | Path,
    *,
    key: str,
    keep: int,
    dry_run: bool = True,
) -> list[Path]:
    if keep < 1:
        raise PortableRecoveryError("portable recovery retention keep must be at least 1")
    reports = verified_portable_bundles(directory, key=key)
    candidates = [report.bundle_path for report in reports[keep:]]
    if dry_run:
        return candidates
    for bundle in candidates:
        try:
            bundle.unlink()
        except OSError as exc:
            raise PortableRecoveryError("portable recovery retention deletion failed") from exc
    return candidates
