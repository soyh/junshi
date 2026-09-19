from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config.settings import get_settings
from app.core.runtime_probe import probe_runtime
from app.core.runtime_watchdog import RuntimeWatchdogError, evaluate_runtime_watchdog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate local runtime health and request recovery only after consecutive failures."
    )
    parser.add_argument(
        "--state-file",
        default="/run/ai-love-strategist/watchdog.json",
        help="Ephemeral watchdog state file.",
    )
    parser.add_argument(
        "--failure-threshold",
        type=int,
        default=3,
        help="Consecutive failures required before recovery is requested.",
    )
    parser.add_argument(
        "--live-every-ticks",
        type=int,
        default=3,
        help="Run liveness every N watchdog ticks; readiness runs every tick.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=2.0,
        help="Local HTTP probe timeout.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()

    def probe(kind):
        return probe_runtime(
            kind,
            host=settings.host,
            port=settings.port,
            timeout_seconds=args.timeout_seconds,
        )

    try:
        report = evaluate_runtime_watchdog(
            Path(args.state_file),
            probe,
            failure_threshold=args.failure_threshold,
            live_every_ticks=args.live_every_ticks,
        )
    except RuntimeWatchdogError as exc:
        payload = {"ok": False, "recovery_required": True, "error": str(exc)}
        if args.as_json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"watchdog: failed ({exc})")
        return 1

    payload = report.to_dict()
    payload["ok"] = not report.recovery_required
    if args.as_json:
        print(json.dumps(payload, sort_keys=True))
    elif report.recovery_required:
        print(f"watchdog: recovery required ({report.trigger})")
    else:
        print("watchdog: healthy")

    return 1 if report.recovery_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
