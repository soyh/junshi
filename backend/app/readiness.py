from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config.settings import get_settings
from app.core.readiness import ReadinessCheckError, check_readiness, default_migration_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run read-only operational readiness checks.")
    parser.add_argument("--database", help="SQLite database path; defaults to DATABASE_PATH.")
    parser.add_argument("--migrations-dir", help="Migration directory; defaults to backend/migrations.")
    parser.add_argument("--backup-dir", help="Managed backup directory; defaults to <database parent>/backups.")
    parser.add_argument(
        "--max-backup-age-hours",
        type=float,
        default=24.0,
        help="Maximum age of latest verified managed backup.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    database = Path(args.database or get_settings().database_path).resolve()
    migrations = Path(args.migrations_dir).resolve() if args.migrations_dir else default_migration_dir()
    backups = Path(args.backup_dir).resolve() if args.backup_dir else database.parent / "backups"

    try:
        report = check_readiness(
            database,
            migration_dir=migrations,
            backup_dir=backups,
            max_backup_age_hours=args.max_backup_age_hours,
        )
    except ReadinessCheckError as exc:
        payload = {"ready": False, "error": str(exc)}
        if args.as_json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"readiness error: {exc}")
        return 1

    payload = report.to_dict()
    if args.as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"ready: {report.ready}")
        print(f"database: {report.database}")
        print(f"migrations: {report.migrations}")
        print(f"backup: {report.backup}")
    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
