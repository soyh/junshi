from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config.settings import get_settings
from app.core.preflight import check_release_preflight
from app.core.readiness import ReadinessCheckError, default_migration_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run release preflight checks without starting the service.")
    parser.add_argument("--database", help="SQLite database path; defaults to DATABASE_PATH.")
    parser.add_argument("--migrations-dir", help="Migration directory; defaults to backend/migrations.")
    parser.add_argument("--backup-dir", help="Managed backup directory; defaults to <database parent>/backups.")
    parser.add_argument("--max-backup-age-hours", type=float, default=24.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    database = Path(args.database or settings.database_path).resolve()
    migrations = Path(args.migrations_dir).resolve() if args.migrations_dir else default_migration_dir()
    backups = Path(args.backup_dir).resolve() if args.backup_dir else database.parent / "backups"

    try:
        report = check_release_preflight(
            settings,
            database_path=database,
            migration_dir=migrations,
            backup_dir=backups,
            max_backup_age_hours=args.max_backup_age_hours,
        )
        payload = report.to_dict()
    except ReadinessCheckError as exc:
        payload = {"ready": False, "error": str(exc)}

    if args.as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"ready: {payload.get('ready', False)}")
        for key, value in payload.items():
            if key != "ready":
                print(f"{key}: {value}")
    return 0 if payload.get("ready") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
