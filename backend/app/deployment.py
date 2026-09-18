from __future__ import annotations

import argparse
import json

from app.config.settings import get_settings
from app.core.deployment import ReleaseRunbookError, build_release_runbook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit the platform-neutral release runbook contract.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        runbook = build_release_runbook(get_settings())
        payload = runbook.to_dict()
    except ReleaseRunbookError as exc:
        payload = {"ready": False, "error": str(exc)}
        if args.as_json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"release runbook error: {exc}")
        return 1

    if args.as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("release runbook schema_version:", payload["schema_version"])
        print("sequence:", " -> ".join(payload["sequence"]))
        print("database restore: manual/offline-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
