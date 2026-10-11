from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import get_settings
from app.core.backup import DatabaseBackupError, verify_database
from app.core.backup_manifest import (
    BackupManifestError,
    apply_retention,
    create_managed_backup,
    verify_backup_manifest,
)


def default_backup_destination(source: str | Path, *, now: datetime | None = None) -> Path:
    source_path = Path(source).resolve()
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    suffix = source_path.suffix or ".sqlite3"
    return source_path.parent / "backups" / f"{source_path.stem}-{timestamp}{suffix}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create, verify, or retain managed SQLite backups.")
    parser.add_argument("--source", help="Source SQLite database path.")
    parser.add_argument("--destination", help="Backup destination path.")
    parser.add_argument(
        "--verify-only",
        metavar="PATH",
        help="Only run PRAGMA integrity_check against PATH; do not create a backup.",
    )
    parser.add_argument(
        "--verify-manifest",
        metavar="PATH",
        help="Verify a managed backup and its manifest/checksum.",
    )
    parser.add_argument("--retention-dir", help="Directory containing managed backup manifests.")
    parser.add_argument("--keep", type=int, help="Number of newest verified managed backups to keep.")
    parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Actually delete retention candidates; default is dry-run.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.verify_only:
            verify_database(args.verify_only)
            print(f"verified: {Path(args.verify_only).resolve()}")
            return 0

        if args.verify_manifest:
            manifest = verify_backup_manifest(args.verify_manifest)
            print(f"managed backup verified: {manifest.backup_filename} sha256={manifest.sha256}")
            return 0

        if args.retention_dir:
            if args.keep is None:
                raise BackupManifestError("--keep is required with --retention-dir")
            candidates = apply_retention(
                args.retention_dir,
                keep=args.keep,
                dry_run=not args.apply_retention,
            )
            mode = "deleted" if args.apply_retention else "candidate"
            for backup_path, manifest_path in candidates:
                print(f"retention {mode}: {backup_path} manifest={manifest_path}")
            print(f"retention {mode} count: {len(candidates)}")
            return 0

        if args.keep is not None or args.apply_retention:
            raise BackupManifestError("retention options require --retention-dir")

        source = Path(args.source or get_settings().database_path).resolve()
        destination = Path(args.destination).resolve() if args.destination else default_backup_destination(source)
        backup_path, manifest_path = create_managed_backup(source, destination)
        print(f"backup created: {backup_path}")
        print(f"manifest created: {manifest_path}")
        return 0
    except (DatabaseBackupError, BackupManifestError) as exc:
        print(f"backup error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
