from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config.settings import get_settings
from app.core.offsite_backup import (
    OffsiteBackupError,
    apply_offsite_retention,
    decode_offsite_key,
    export_latest_managed_backup,
    generate_offsite_key,
    latest_verified_managed_backup,
    require_separate_storage,
    verify_offsite_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and verify encrypted offsite copies of verified managed SQLite backups."
    )
    parser.add_argument("--generate-key", action="store_true")
    parser.add_argument("--check", action="store_true", help="Validate offsite configuration without writing.")
    parser.add_argument("--verify", metavar="PATH", help="Verify an encrypted offsite bundle.")
    parser.add_argument("--local-dir", help="Managed local backup directory.")
    parser.add_argument("--destination-dir", help="Mounted offsite destination directory.")
    parser.add_argument("--key", help="Override OFFSITE_BACKUP_ENCRYPTION_KEY.")
    parser.add_argument("--keep", type=int, help="Verified offsite bundles to retain.")
    parser.add_argument("--apply-retention", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _emit(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")


def _configuration(args) -> tuple[Path, Path, str, int]:
    settings = get_settings()
    database_path = Path(settings.database_path).resolve()
    local_dir = Path(args.local_dir).resolve() if args.local_dir else database_path.parent / "backups"
    destination_raw = args.destination_dir or settings.offsite_backup_directory
    if not destination_raw:
        raise OffsiteBackupError("offsite backup destination directory is not configured")
    destination_dir = Path(destination_raw).resolve()
    key = args.key or settings.offsite_backup_encryption_key
    decode_offsite_key(key)
    keep = args.keep if args.keep is not None else settings.offsite_backup_keep
    if keep < 1:
        raise OffsiteBackupError("offsite backup retention keep must be at least 1")
    return local_dir, destination_dir, str(key), keep


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.generate_key:
        print(generate_offsite_key())
        return 0

    try:
        local_dir, destination_dir, key, keep = _configuration(args)

        if args.verify:
            report = verify_offsite_bundle(args.verify, key=key)
            _emit(
                {
                    "ok": True,
                    "bundle": str(report.bundle_path),
                    "bundle_sha256": report.bundle_sha256,
                    "source_backup_filename": report.source_backup_filename,
                    "source_sha256": report.source_sha256,
                },
                as_json=args.as_json,
            )
            return 0

        backup_path, manifest_path = latest_verified_managed_backup(local_dir)
        require_separate_storage(backup_path, destination_dir)

        if args.check:
            _emit(
                {
                    "ok": True,
                    "local_backup": str(backup_path),
                    "local_manifest": str(manifest_path),
                    "offsite_directory": str(destination_dir),
                    "separate_storage": True,
                    "retention_keep": keep,
                },
                as_json=args.as_json,
            )
            return 0

        report = export_latest_managed_backup(
            local_dir,
            destination_dir,
            key=key,
            require_distinct_storage=True,
        )
        deleted = apply_offsite_retention(
            destination_dir,
            key=key,
            keep=keep,
            dry_run=not args.apply_retention,
        )
        _emit(
            {
                "ok": True,
                "bundle": str(report.bundle_path),
                "bundle_sha256": report.bundle_sha256,
                "source_backup_filename": report.source_backup_filename,
                "source_sha256": report.source_sha256,
                "retention_mode": "applied" if args.apply_retention else "dry-run",
                "retention_count": len(deleted),
            },
            as_json=args.as_json,
        )
        return 0
    except OffsiteBackupError as exc:
        _emit({"ok": False, "error": str(exc)}, as_json=args.as_json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
