from __future__ import annotations

import argparse
import json

from app.config.settings import get_settings
from app.core.runtime_probe import RuntimeProbeError, probe_runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe the local application liveness or readiness endpoint."
    )
    parser.add_argument("kind", choices=("live", "ready"))
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=2.0,
        help="Local HTTP probe timeout in seconds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()

    try:
        result = probe_runtime(
            args.kind,
            host=settings.host,
            port=settings.port,
            timeout_seconds=args.timeout_seconds,
        )
    except RuntimeProbeError as exc:
        payload = {
            "kind": args.kind,
            "ok": False,
            "status_code": None,
            "error": str(exc),
        }
        if args.as_json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"{args.kind}: failed ({exc})")
        return 1

    payload = result.to_dict()
    if args.as_json:
        print(json.dumps(payload, sort_keys=True))
    elif result.ok:
        print(f"{result.kind}: ok")
    else:
        print(f"{result.kind}: failed ({result.error})")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
