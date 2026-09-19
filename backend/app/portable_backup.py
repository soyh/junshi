from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.backup import default_backup_destination
from app.config.settings import get_settings
from app.core.backup_manifest import BackupManifestError, create_managed_backup
from app.core.portable_recovery import (
    PortableRecoveryError,
    apply_portable_retention,
    create_or_reuse_portable_bundle,
    ensure_private_directory,
    extract_portable_bundle,
    generate_portable_key,
    validate_portable_key,
    verify_portable_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create, verify, and extract portable encrypted recovery bundles."
    )
    parser.add_argument("--generate-key", action="store_true")
    parser.add_argument("--prepare", action="store_true", help="Create a fresh managed DB backup and encrypted recovery bundle.")
    parser.add_argument("--check", action="store_true", help="Validate portable recovery configuration without writing a bundle.")
    parser.add_argument("--verify", metavar="PATH", help="Verify an encrypted recovery bundle.")
    parser.add_argument("--extract", metavar="PATH", help="Extract an encrypted recovery bundle into a private directory.")
    parser.add_argument("--destination-dir", help="Extraction destination directory.")
    parser.add_argument("--local-dir", help="Managed local backup directory.")
    parser.add_argument("--export-dir", help="Portable recovery bundle directory.")
    parser.add_argument("--key", help="Override PORTABLE_BACKUP_ENCRYPTION_KEY.")
    parser.add_argument("--keep", type=int, help="Portable recovery bundles to retain on the server.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _emit(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")


def _configuration(args) -> tuple[Path, Path, str, int, Path]:
    settings = get_settings()
    database_path = Path(settings.database_path).resolve()
    local_dir = Path(args.local_dir).resolve() if args.local_dir else database_path.parent / "backups"
    export_dir = Path(args.export_dir or settings.portable_backup_directory).resolve()
    key = validate_portable_key(args.key or settings.portable_backup_encryption_key)
    keep = args.keep if args.keep is not None else settings.portable_backup_keep
    if keep < 1:
        raise PortableRecoveryError("portable backup retention keep must be at least 1")
    return local_dir, export_dir, key, keep, database_path


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.generate_key:
        print(generate_portable_key())
        return 0

    try:
        local_dir, export_dir, key, keep, database_path = _configuration(args)

        if args.verify:
            report = verify_portable_bundle(args.verify, key=key)
            _emit(
                {
                    "ok": True,
                    "bundle": str(report.bundle_path),
                    "bundle_sha256": report.bundle_sha256,
                    "source_backup_filename": report.source_backup_filename,
                    "source_created_at": report.source_created_at,
                    "source_sha256": report.source_sha256,
                },
                as_json=args.as_json,
            )
            return 0

        if args.extract:
            if not args.destination_dir:
                raise PortableRecoveryError("--destination-dir is required with --extract")
            backup_path, manifest_path, report = extract_portable_bundle(
                args.extract,
                args.destination_dir,
                key=key,
            )
            _emit(
                {
                    "ok": True,
                    "backup": str(backup_path),
                    "manifest": str(manifest_path),
                    "source_sha256": report.source_sha256,
                },
                as_json=args.as_json,
            )
            return 0

        if args.check:
            ensure_private_directory(export_dir)
            _emit(
                {
                    "ok": True,
                    "database": str(database_path),
                    "local_backup_directory": str(local_dir),
                    "portable_export_directory": str(export_dir),
                    "retention_keep": keep,
                },
                as_json=args.as_json,
            )
            return 0

        if not args.prepare:
            raise PortableRecoveryError("one of --prepare, --check, --verify, --extract, or --generate-key is required")

        local_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        default_destination = default_backup_destination(database_path)
        destination = local_dir / default_destination.name
        try:
            backup_path, manifest_path = create_managed_backup(database_path, destination)
        except BackupManifestError as exc:
            raise PortableRecoveryError("fresh managed backup creation failed") from exc

        result = create_or_reuse_portable_bundle(local_dir, export_dir, key=key)
        deleted = apply_portable_retention(
            export_dir,
            key=key,
            keep=keep,
            dry_run=False,
        )
        report = result.report
        _emit(
            {
                "ok": True,
                "bundle": str(report.bundle_path),
                "bundle_sha256": report.bundle_sha256,
                "source_backup": str(backup_path),
                "source_manifest": str(manifest_path),
                "source_backup_filename": report.source_backup_filename,
                "source_created_at": report.source_created_at,
                "source_sha256": report.source_sha256,
                "reused_existing": result.reused_existing,
                "server_retention_deleted": len(deleted),
            },
            as_json=args.as_json,
        )
        return 0
    except (PortableRecoveryError, OSError) as exc:
        _emit({"ok": False, "error": str(exc)}, as_json=args.as_json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
