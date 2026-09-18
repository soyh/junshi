from __future__ import annotations

import argparse
from pathlib import Path

from app.config.settings import get_settings
from app.core.restore import DatabaseRestoreError, restore_verified_backup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Restore a verified SQLite backup while the application is offline.")
    parser.add_argument("--backup", required=True, help="Verified SQLite backup path.")
    parser.add_argument("--destination", help="Destination database path. Defaults to DATABASE_PATH.")
    parser.add_argument(
        "--offline-confirmed",
        action="store_true",
        help="Required acknowledgement that the application/database is fully offline.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    destination = Path(args.destination or get_settings().database_path).resolve()

    try:
        restored = restore_verified_backup(
            args.backup,
            destination,
            offline_confirmed=args.offline_confirmed,
        )
        print(f"restore complete: {restored}")
        return 0
    except DatabaseRestoreError as exc:
        print(f"restore error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
