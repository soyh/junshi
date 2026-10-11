from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.core.backup import DatabaseBackupError, create_verified_backup, verify_database


MANIFEST_SCHEMA_VERSION = 1
MANIFEST_SUFFIX = ".manifest.json"


class BackupManifestError(RuntimeError):
    """Raised when backup metadata cannot be safely created or verified."""


@dataclass(frozen=True)
class BackupManifest:
    schema_version: int
    created_at: str
    backup_filename: str
    size_bytes: int
    sha256: str
    integrity: str


def manifest_path_for(backup: str | Path) -> Path:
    backup_path = Path(backup).resolve()
    return backup_path.with_name(f"{backup_path.name}{MANIFEST_SUFFIX}")


def _utc_now_iso(now: datetime | None = None) -> str:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BackupManifestError("manifest created_at is invalid") from exc
    if parsed.tzinfo is None:
        raise BackupManifestError("manifest created_at must include timezone")
    return parsed.astimezone(timezone.utc)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_directory(directory: Path) -> None:
    try:
        directory_fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    if path.exists():
        raise BackupManifestError(f"manifest already exists: {path}")

    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        with temporary_path.open("xb") as target:
            target.write(encoded)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, path)
        _fsync_directory(path.parent)
    except BackupManifestError:
        raise
    except OSError as exc:
        raise BackupManifestError("manifest publish failed") from exc
    finally:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass


def write_backup_manifest(
    backup: str | Path,
    *,
    now: datetime | None = None,
) -> Path:
    backup_path = Path(backup).resolve()
    if not backup_path.is_file():
        raise BackupManifestError(f"backup does not exist: {backup_path}")

    try:
        verify_database(backup_path)
    except DatabaseBackupError as exc:
        raise BackupManifestError("backup integrity verification failed") from exc

    manifest_path = manifest_path_for(backup_path)
    payload = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": _utc_now_iso(now),
        "backup_filename": backup_path.name,
        "size_bytes": backup_path.stat().st_size,
        "sha256": _sha256_file(backup_path),
        "integrity": "ok",
    }
    _atomic_write_json(manifest_path, payload)
    return manifest_path


def _load_manifest(path: Path) -> BackupManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupManifestError("manifest is unreadable") from exc

    if not isinstance(raw, dict):
        raise BackupManifestError("manifest must be a JSON object")

    expected = {"schema_version", "created_at", "backup_filename", "size_bytes", "sha256", "integrity"}
    if set(raw) != expected:
        raise BackupManifestError("manifest fields do not match schema")

    try:
        manifest = BackupManifest(
            schema_version=int(raw["schema_version"]),
            created_at=str(raw["created_at"]),
            backup_filename=str(raw["backup_filename"]),
            size_bytes=int(raw["size_bytes"]),
            sha256=str(raw["sha256"]),
            integrity=str(raw["integrity"]),
        )
    except (TypeError, ValueError) as exc:
        raise BackupManifestError("manifest field types are invalid") from exc

    if manifest.schema_version != MANIFEST_SCHEMA_VERSION:
        raise BackupManifestError("unsupported manifest schema version")
    if Path(manifest.backup_filename).name != manifest.backup_filename:
        raise BackupManifestError("manifest backup filename must be a basename")
    if manifest.size_bytes < 0:
        raise BackupManifestError("manifest size is invalid")
    if len(manifest.sha256) != 64 or any(ch not in "0123456789abcdef" for ch in manifest.sha256):
        raise BackupManifestError("manifest sha256 is invalid")
    if manifest.integrity != "ok":
        raise BackupManifestError("manifest integrity status is not ok")
    _parse_utc_timestamp(manifest.created_at)
    return manifest


def verify_backup_manifest(path: str | Path) -> BackupManifest:
    supplied_path = Path(path).resolve()
    manifest_path = supplied_path if supplied_path.name.endswith(MANIFEST_SUFFIX) else manifest_path_for(supplied_path)
    if not manifest_path.is_file():
        raise BackupManifestError(f"manifest does not exist: {manifest_path}")

    manifest = _load_manifest(manifest_path)
    backup_path = manifest_path.parent / manifest.backup_filename
    if not backup_path.is_file():
        raise BackupManifestError("manifest backup file does not exist")
    if backup_path.stat().st_size != manifest.size_bytes:
        raise BackupManifestError("backup size does not match manifest")
    if _sha256_file(backup_path) != manifest.sha256:
        raise BackupManifestError("backup checksum does not match manifest")

    try:
        verify_database(backup_path)
    except DatabaseBackupError as exc:
        raise BackupManifestError("backup database integrity verification failed") from exc
    return manifest


def create_managed_backup(
    source: str | Path,
    destination: str | Path,
    *,
    now: datetime | None = None,
) -> tuple[Path, Path]:
    destination_path = Path(destination).resolve()
    manifest_path = manifest_path_for(destination_path)
    if manifest_path.exists():
        raise BackupManifestError(f"manifest already exists: {manifest_path}")

    backup_created = False
    try:
        backup_path = create_verified_backup(source, destination_path)
        backup_created = True
        created_manifest = write_backup_manifest(backup_path, now=now)
        return backup_path, created_manifest
    except (DatabaseBackupError, BackupManifestError) as exc:
        if backup_created:
            try:
                destination_path.unlink(missing_ok=True)
                _fsync_directory(destination_path.parent)
            except OSError:
                pass
        if isinstance(exc, BackupManifestError):
            raise
        raise BackupManifestError("managed backup creation failed") from exc


def _verified_managed_backups(directory: Path) -> list[tuple[datetime, Path, Path]]:
    verified: list[tuple[datetime, Path, Path]] = []
    for manifest_path in directory.glob(f"*{MANIFEST_SUFFIX}"):
        try:
            manifest = verify_backup_manifest(manifest_path)
        except BackupManifestError:
            continue
        backup_path = directory / manifest.backup_filename
        verified.append((_parse_utc_timestamp(manifest.created_at), backup_path, manifest_path))
    verified.sort(key=lambda item: (item[0], item[1].name), reverse=True)
    return verified


def retention_candidates(directory: str | Path, *, keep: int) -> list[tuple[Path, Path]]:
    if keep < 1:
        raise BackupManifestError("retention keep must be at least 1")
    directory_path = Path(directory).resolve()
    if not directory_path.is_dir():
        raise BackupManifestError(f"retention directory does not exist: {directory_path}")
    verified = _verified_managed_backups(directory_path)
    return [(backup, manifest) for _, backup, manifest in verified[keep:]]


def apply_retention(
    directory: str | Path,
    *,
    keep: int,
    dry_run: bool = True,
) -> list[tuple[Path, Path]]:
    candidates = retention_candidates(directory, keep=keep)
    if dry_run:
        return candidates

    directory_path = Path(directory).resolve()
    for backup_path, manifest_path in candidates:
        try:
            manifest_path.unlink()
            backup_path.unlink(missing_ok=True)
        except OSError as exc:
            raise BackupManifestError("retention deletion failed") from exc
    _fsync_directory(directory_path)
    return candidates
