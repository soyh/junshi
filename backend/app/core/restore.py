from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from app.core.backup import DatabaseBackupError, verify_database


class DatabaseRestoreError(RuntimeError):
    """Raised when a database restore cannot be completed safely."""


def _fsync_directory(path: Path) -> None:
    try:
        directory_fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def restore_verified_backup(
    backup: str | Path,
    destination: str | Path,
    *,
    offline_confirmed: bool = False,
) -> Path:
    """Atomically restore a verified SQLite backup to an offline destination.

    The caller must explicitly confirm that the application/database is offline.
    The backup is verified before the existing destination is touched. A sibling
    temporary copy is verified and fsynced before atomic replacement. Stale WAL
    and SHM sidecars are removed only after the replacement succeeds.
    """
    backup_path = Path(backup).resolve()
    destination_path = Path(destination).resolve()

    if not offline_confirmed:
        raise DatabaseRestoreError("restore requires explicit offline confirmation")
    if backup_path == destination_path:
        raise DatabaseRestoreError("backup and destination must be different files")

    try:
        verify_database(backup_path)
    except DatabaseBackupError as exc:
        raise DatabaseRestoreError("backup verification failed") from exc

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_path.with_name(
        f".{destination_path.name}.{uuid.uuid4().hex}.restore.tmp"
    )

    try:
        shutil.copyfile(backup_path, temporary_path)
        os.chmod(temporary_path, 0o600)

        try:
            verify_database(temporary_path)
        except DatabaseBackupError as exc:
            raise DatabaseRestoreError("restore candidate verification failed") from exc

        with temporary_path.open("rb") as restored_file:
            os.fsync(restored_file.fileno())

        os.replace(temporary_path, destination_path)

        for suffix in ("-wal", "-shm"):
            sidecar = Path(f"{destination_path}{suffix}")
            try:
                sidecar.unlink(missing_ok=True)
            except OSError as exc:
                raise DatabaseRestoreError(f"failed to remove stale SQLite sidecar: {sidecar}") from exc

        _fsync_directory(destination_path.parent)

        try:
            verify_database(destination_path)
        except DatabaseBackupError as exc:
            raise DatabaseRestoreError("restored database verification failed") from exc

        return destination_path
    except DatabaseRestoreError:
        raise
    except OSError as exc:
        raise DatabaseRestoreError("database restore failed") from exc
    finally:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
