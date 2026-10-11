from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from typing import Callable

from app.config.settings import get_settings
from app.core.runtime_probe import RuntimeProbeError, RuntimeProbeResult, probe_runtime


@dataclass(frozen=True)
class StartupReadinessResult:
    ok: bool
    attempts: int
    elapsed_seconds: float
    status_code: int | None
    error: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def wait_until_ready(
    *,
    host: str,
    port: int,
    timeout_seconds: float = 30.0,
    interval_seconds: float = 0.5,
    probe_timeout_seconds: float = 1.0,
    probe: Callable[..., RuntimeProbeResult] = probe_runtime,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> StartupReadinessResult:
    if timeout_seconds <= 0:
        raise RuntimeProbeError("startup readiness timeout must be positive")
    if interval_seconds <= 0:
        raise RuntimeProbeError("startup readiness interval must be positive")
    if probe_timeout_seconds <= 0:
        raise RuntimeProbeError("startup readiness probe timeout must be positive")

    started = monotonic()
    deadline = started + timeout_seconds
    attempts = 0
    last_result: RuntimeProbeResult | None = None

    while True:
        attempts += 1
        last_result = probe(
            "ready",
            host=host,
            port=port,
            timeout_seconds=probe_timeout_seconds,
        )

        if last_result.ok:
            return StartupReadinessResult(
                ok=True,
                attempts=attempts,
                elapsed_seconds=max(0.0, monotonic() - started),
                status_code=last_result.status_code,
                error=None,
            )

        now = monotonic()
        if now >= deadline:
            return StartupReadinessResult(
                ok=False,
                attempts=attempts,
                elapsed_seconds=max(0.0, now - started),
                status_code=last_result.status_code,
                error=last_result.error or "service did not become ready",
            )

        sleep(min(interval_seconds, deadline - now))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wait for the local application readiness endpoint during startup."
    )
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--interval-seconds", type=float, default=0.5)
    parser.add_argument("--probe-timeout-seconds", type=float, default=1.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()

    try:
        result = wait_until_ready(
            host=settings.host,
            port=settings.port,
            timeout_seconds=args.timeout_seconds,
            interval_seconds=args.interval_seconds,
            probe_timeout_seconds=args.probe_timeout_seconds,
        )
    except RuntimeProbeError as exc:
        payload = {
            "ok": False,
            "attempts": 0,
            "elapsed_seconds": 0.0,
            "status_code": None,
            "error": str(exc),
        }
        if args.as_json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"startup readiness: failed ({exc})")
        return 1

    payload = result.to_dict()
    if args.as_json:
        print(json.dumps(payload, sort_keys=True))
    elif result.ok:
        print(f"startup readiness: ok after {result.attempts} attempt(s)")
    else:
        print(f"startup readiness: failed ({result.error})")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
