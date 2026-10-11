from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path


class DatabaseBackupError(RuntimeError):
    """Raised when a database backup cannot be safely created or verified."""


def _readonly_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def verify_database(path: str | Path) -> None:
    """Raise DatabaseBackupError unless SQLite reports an intact database."""
    database_path = Path(path).resolve()
    if not database_path.is_file():
        raise DatabaseBackupError(f"database does not exist: {database_path}")

    try:
        with sqlite3.connect(_readonly_uri(database_path), uri=True, timeout=5.0) as conn:
            rows = conn.execute("PRAGMA integrity_check").fetchall()
    except sqlite3.DatabaseError as exc:
        raise DatabaseBackupError(f"database integrity check failed: {database_path}") from exc

    results = [str(row[0]) for row in rows]
    if results != ["ok"]:
        detail = "; ".join(results) if results else "no integrity_check result"
        raise DatabaseBackupError(f"database integrity check failed: {detail}")


def create_verified_backup(
    source: str | Path,
    destination: str | Path,
) -> Path:
    """Create and atomically publish a verified SQLite online backup.

    The source is opened read-only. SQLite's online backup API provides a
    consistent snapshot even when the source uses WAL mode. The destination is
    first written to a sibling temporary file, integrity-checked, fsynced, and
    only then atomically moved into place.
    """
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()

    if not source_path.is_file():
        raise DatabaseBackupError(f"source database does not exist: {source_path}")
    if source_path == destination_path:
        raise DatabaseBackupError("source and destination must be different files")
    if destination_path.exists():
        raise DatabaseBackupError(f"destination already exists: {destination_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_path.with_name(
        f".{destination_path.name}.{uuid.uuid4().hex}.tmp"
    )

    try:
        source_conn = sqlite3.connect(_readonly_uri(source_path), uri=True, timeout=5.0)
        try:
            destination_conn = sqlite3.connect(temporary_path, timeout=5.0)
            try:
                source_conn.backup(destination_conn)
                destination_conn.commit()
            finally:
                destination_conn.close()
        finally:
            source_conn.close()

        verify_database(temporary_path)

        with temporary_path.open("rb") as backup_file:
            os.fsync(backup_file.fileno())

        os.replace(temporary_path, destination_path)

        try:
            directory_fd = os.open(destination_path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

        return destination_path
    except DatabaseBackupError:
        raise
    except (OSError, sqlite3.DatabaseError) as exc:
        raise DatabaseBackupError("database backup failed") from exc
    finally:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
