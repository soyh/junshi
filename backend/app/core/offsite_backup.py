from __future__ import annotations

import base64
import hashlib
import json
import os
import struct
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.core.backup_manifest import MANIFEST_SUFFIX, BackupManifestError, verify_backup_manifest


OFFSITE_MAGIC = b"ALS-OFFSITE-1\n"
OFFSITE_NONCE_BYTES = 12
OFFSITE_TAG_BYTES = 16
OFFSITE_KEY_BYTES = 32
OFFSITE_CHUNK_BYTES = 1024 * 1024
OFFSITE_SUFFIX = ".offsite.enc"
MAX_MANIFEST_BYTES = 1024 * 1024


class OffsiteBackupError(RuntimeError):
    """Raised when encrypted offsite backup creation or verification is unsafe."""


@dataclass(frozen=True)
class OffsiteBundleReport:
    bundle_path: Path
    bundle_size_bytes: int
    bundle_sha256: str
    source_backup_filename: str
    source_created_at: str
    source_sha256: str
    source_size_bytes: int


def generate_offsite_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(OFFSITE_KEY_BYTES)).decode("ascii")


def decode_offsite_key(value: str | None) -> bytes:
    if not value:
        raise OffsiteBackupError("offsite backup encryption key is not configured")
    try:
        decoded = base64.urlsafe_b64decode(value.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise OffsiteBackupError("offsite backup encryption key is invalid") from exc
    if len(decoded) != OFFSITE_KEY_BYTES:
        raise OffsiteBackupError("offsite backup encryption key must decode to 32 bytes")
    return decoded


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(OFFSITE_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_directory(directory: Path) -> None:
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _parse_created_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OffsiteBackupError("managed backup created_at is invalid") from exc
    if parsed.tzinfo is None:
        raise OffsiteBackupError("managed backup created_at must include timezone")
    return parsed.astimezone(timezone.utc)


def latest_verified_managed_backup(directory: str | Path) -> tuple[Path, Path]:
    directory_path = Path(directory).resolve()
    if not directory_path.is_dir():
        raise OffsiteBackupError(f"managed backup directory does not exist: {directory_path}")

    verified: list[tuple[datetime, Path, Path]] = []
    for manifest_path in directory_path.glob(f"*{MANIFEST_SUFFIX}"):
        try:
            manifest = verify_backup_manifest(manifest_path)
            created_at = _parse_created_at(manifest.created_at)
        except (BackupManifestError, OffsiteBackupError):
            continue
        verified.append((created_at, directory_path / manifest.backup_filename, manifest_path))

    if not verified:
        raise OffsiteBackupError("no verified managed backup is available for offsite export")

    verified.sort(key=lambda item: (item[0], item[1].name), reverse=True)
    _, backup_path, manifest_path = verified[0]
    return backup_path, manifest_path


def require_separate_storage(source: str | Path, destination_directory: str | Path) -> None:
    source_path = Path(source).resolve()
    destination_path = Path(destination_directory).resolve()
    if not source_path.is_file():
        raise OffsiteBackupError(f"source backup does not exist: {source_path}")
    if not destination_path.is_dir():
        raise OffsiteBackupError(f"offsite destination directory does not exist: {destination_path}")
    try:
        source_device = source_path.stat().st_dev
        destination_device = destination_path.stat().st_dev
    except OSError as exc:
        raise OffsiteBackupError("offsite storage device check failed") from exc
    if source_device == destination_device:
        raise OffsiteBackupError("offsite destination must be on storage separate from the database backup")


def _read_manifest_bytes(manifest_path: Path) -> bytes:
    try:
        raw = manifest_path.read_bytes()
    except OSError as exc:
        raise OffsiteBackupError("managed backup manifest cannot be read") from exc
    if not raw or len(raw) > MAX_MANIFEST_BYTES:
        raise OffsiteBackupError("managed backup manifest size is invalid")
    return raw


def create_encrypted_offsite_bundle(
    backup: str | Path,
    manifest: str | Path,
    destination: str | Path,
    *,
    key: str | bytes,
) -> OffsiteBundleReport:
    backup_path = Path(backup).resolve()
    manifest_path = Path(manifest).resolve()
    destination_path = Path(destination).resolve()

    try:
        managed = verify_backup_manifest(manifest_path)
    except BackupManifestError as exc:
        raise OffsiteBackupError("source managed backup verification failed") from exc

    if backup_path != manifest_path.parent / managed.backup_filename:
        raise OffsiteBackupError("source backup and manifest do not form the same managed backup pair")
    if destination_path.exists():
        raise OffsiteBackupError(f"offsite bundle already exists: {destination_path}")
    if not destination_path.parent.is_dir():
        raise OffsiteBackupError(f"offsite destination directory does not exist: {destination_path.parent}")

    encryption_key = decode_offsite_key(key.decode("ascii") if isinstance(key, bytes) else key)
    manifest_bytes = _read_manifest_bytes(manifest_path)
    nonce = os.urandom(OFFSITE_NONCE_BYTES)
    temporary_path = destination_path.with_name(f".{destination_path.name}.{uuid.uuid4().hex}.tmp")

    try:
        encryptor = Cipher(algorithms.AES(encryption_key), modes.GCM(nonce)).encryptor()
        encryptor.authenticate_additional_data(OFFSITE_MAGIC)

        with temporary_path.open("xb") as target, backup_path.open("rb") as source:
            target.write(OFFSITE_MAGIC)
            target.write(nonce)
            target.write(encryptor.update(struct.pack(">Q", len(manifest_bytes))))
            target.write(encryptor.update(manifest_bytes))
            for chunk in iter(lambda: source.read(OFFSITE_CHUNK_BYTES), b""):
                target.write(encryptor.update(chunk))
            tail = encryptor.finalize()
            if tail:
                target.write(tail)
            target.write(encryptor.tag)
            target.flush()
            os.fsync(target.fileno())

        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, destination_path)
        _fsync_directory(destination_path.parent)
    except (OSError, ValueError) as exc:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise OffsiteBackupError("encrypted offsite bundle publish failed") from exc

    try:
        return verify_offsite_bundle(destination_path, key=key)
    except OffsiteBackupError:
        try:
            destination_path.unlink(missing_ok=True)
            _fsync_directory(destination_path.parent)
        except OSError:
            pass
        raise


def _decrypt_bundle_to_payload(bundle_path: Path, payload_path: Path, encryption_key: bytes) -> None:
    try:
        total_size = bundle_path.stat().st_size
    except OSError as exc:
        raise OffsiteBackupError("offsite bundle cannot be stat-ed") from exc

    minimum_size = len(OFFSITE_MAGIC) + OFFSITE_NONCE_BYTES + OFFSITE_TAG_BYTES + 8
    if total_size < minimum_size:
        raise OffsiteBackupError("offsite bundle is too small")

    try:
        with bundle_path.open("rb") as source:
            magic = source.read(len(OFFSITE_MAGIC))
            if magic != OFFSITE_MAGIC:
                raise OffsiteBackupError("offsite bundle magic is invalid")
            nonce = source.read(OFFSITE_NONCE_BYTES)
            source.seek(total_size - OFFSITE_TAG_BYTES)
            tag = source.read(OFFSITE_TAG_BYTES)
            ciphertext_start = len(OFFSITE_MAGIC) + OFFSITE_NONCE_BYTES
            ciphertext_end = total_size - OFFSITE_TAG_BYTES
            source.seek(ciphertext_start)

            decryptor = Cipher(algorithms.AES(encryption_key), modes.GCM(nonce, tag)).decryptor()
            decryptor.authenticate_additional_data(OFFSITE_MAGIC)

            remaining = ciphertext_end - ciphertext_start
            with payload_path.open("xb") as target:
                while remaining:
                    chunk = source.read(min(OFFSITE_CHUNK_BYTES, remaining))
                    if not chunk:
                        raise OffsiteBackupError("offsite bundle ciphertext is truncated")
                    remaining -= len(chunk)
                    target.write(decryptor.update(chunk))
                tail = decryptor.finalize()
                if tail:
                    target.write(tail)
                target.flush()
                os.fsync(target.fileno())
    except InvalidTag as exc:
        raise OffsiteBackupError("offsite bundle authentication failed") from exc
    except OffsiteBackupError:
        raise
    except (OSError, ValueError) as exc:
        raise OffsiteBackupError("offsite bundle decryption failed") from exc


def verify_offsite_bundle(bundle: str | Path, *, key: str | bytes) -> OffsiteBundleReport:
    bundle_path = Path(bundle).resolve()
    if not bundle_path.is_file():
        raise OffsiteBackupError(f"offsite bundle does not exist: {bundle_path}")
    encryption_key = decode_offsite_key(key.decode("ascii") if isinstance(key, bytes) else key)

    with tempfile.TemporaryDirectory(prefix="als-offsite-verify-") as temporary_directory:
        temp_dir = Path(temporary_directory)
        payload_path = temp_dir / "payload.bin"
        _decrypt_bundle_to_payload(bundle_path, payload_path, encryption_key)

        try:
            with payload_path.open("rb") as payload:
                length_raw = payload.read(8)
                if len(length_raw) != 8:
                    raise OffsiteBackupError("offsite bundle payload header is truncated")
                manifest_length = struct.unpack(">Q", length_raw)[0]
                if manifest_length < 1 or manifest_length > MAX_MANIFEST_BYTES:
                    raise OffsiteBackupError("offsite bundle manifest length is invalid")
                manifest_bytes = payload.read(manifest_length)
                if len(manifest_bytes) != manifest_length:
                    raise OffsiteBackupError("offsite bundle manifest is truncated")
                try:
                    raw_manifest = json.loads(manifest_bytes.decode("utf-8"))
                    backup_filename = str(raw_manifest["backup_filename"])
                except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
                    raise OffsiteBackupError("offsite bundle manifest payload is invalid") from exc
                if Path(backup_filename).name != backup_filename:
                    raise OffsiteBackupError("offsite bundle backup filename is unsafe")

                backup_path = temp_dir / backup_filename
                manifest_path = temp_dir / f"{backup_filename}{MANIFEST_SUFFIX}"
                manifest_path.write_bytes(manifest_bytes)
                with backup_path.open("xb") as backup_target:
                    for chunk in iter(lambda: payload.read(OFFSITE_CHUNK_BYTES), b""):
                        backup_target.write(chunk)

            try:
                managed = verify_backup_manifest(manifest_path)
            except BackupManifestError as exc:
                raise OffsiteBackupError("offsite bundle managed backup verification failed") from exc
        except OSError as exc:
            raise OffsiteBackupError("offsite bundle payload materialization failed") from exc

    return OffsiteBundleReport(
        bundle_path=bundle_path,
        bundle_size_bytes=bundle_path.stat().st_size,
        bundle_sha256=_sha256_file(bundle_path),
        source_backup_filename=managed.backup_filename,
        source_created_at=managed.created_at,
        source_sha256=managed.sha256,
        source_size_bytes=managed.size_bytes,
    )


def export_latest_managed_backup(
    local_backup_directory: str | Path,
    offsite_directory: str | Path,
    *,
    key: str | bytes,
    require_distinct_storage: bool = True,
) -> OffsiteBundleReport:
    local_directory = Path(local_backup_directory).resolve()
    offsite_path = Path(offsite_directory).resolve()
    backup_path, manifest_path = latest_verified_managed_backup(local_directory)
    if require_distinct_storage:
        require_separate_storage(backup_path, offsite_path)
    destination = offsite_path / f"{backup_path.name}{OFFSITE_SUFFIX}"
    return create_encrypted_offsite_bundle(backup_path, manifest_path, destination, key=key)


def verified_offsite_bundles(directory: str | Path, *, key: str | bytes) -> list[OffsiteBundleReport]:
    directory_path = Path(directory).resolve()
    if not directory_path.is_dir():
        raise OffsiteBackupError(f"offsite destination directory does not exist: {directory_path}")
    verified: list[OffsiteBundleReport] = []
    for bundle_path in directory_path.glob(f"*{OFFSITE_SUFFIX}"):
        try:
            verified.append(verify_offsite_bundle(bundle_path, key=key))
        except OffsiteBackupError:
            continue
    verified.sort(
        key=lambda report: (_parse_created_at(report.source_created_at), report.bundle_path.name),
        reverse=True,
    )
    return verified


def apply_offsite_retention(
    directory: str | Path,
    *,
    key: str | bytes,
    keep: int,
    dry_run: bool = True,
) -> list[Path]:
    if keep < 1:
        raise OffsiteBackupError("offsite retention keep must be at least 1")
    verified = verified_offsite_bundles(directory, key=key)
    candidates = [report.bundle_path for report in verified[keep:]]
    if dry_run:
        return candidates
    for bundle_path in candidates:
        try:
            bundle_path.unlink()
        except OSError as exc:
            raise OffsiteBackupError("offsite retention deletion failed") from exc
    _fsync_directory(Path(directory).resolve())
    return candidates
