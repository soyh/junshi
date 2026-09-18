from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import get_settings
from app.core.backup import DatabaseBackupError, create_verified_backup, verify_database


def default_backup_destination(source: str | Path, *, now: datetime | None = None) -> Path:
    source_path = Path(source).resolve()
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    suffix = source_path.suffix or ".sqlite3"
    return source_path.parent / "backups" / f"{source_path.stem}-{timestamp}{suffix}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or verify a SQLite database backup.")
    parser.add_argument("--source", help="Source SQLite database path.")
    parser.add_argument("--destination", help="Backup destination path.")
    parser.add_argument(
        "--verify-only",
        metavar="PATH",
        help="Only run PRAGMA integrity_check against PATH; do not create a backup.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.verify_only:
            verify_database(args.verify_only)
            print(f"verified: {Path(args.verify_only).resolve()}")
            return 0

        source = Path(args.source or get_settings().database_path).resolve()
        destination = Path(args.destination).resolve() if args.destination else default_backup_destination(source)
        created = create_verified_backup(source, destination)
        print(f"backup created: {created}")
        return 0
    except DatabaseBackupError as exc:
        print(f"backup error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
