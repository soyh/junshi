from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from app.core.runtime_probe import ProbeKind, RuntimeProbeResult


class RuntimeWatchdogError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeWatchdogState:
    tick: int = 0
    live_failures: int = 0
    ready_failures: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeWatchdogReport:
    state: RuntimeWatchdogState
    live: RuntimeProbeResult | None
    ready: RuntimeProbeResult
    failure_threshold: int
    live_every_ticks: int
    recovery_required: bool
    trigger: str | None
    state_reset: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state.to_dict(),
            "live": self.live.to_dict() if self.live is not None else None,
            "ready": self.ready.to_dict(),
            "failure_threshold": self.failure_threshold,
            "live_every_ticks": self.live_every_ticks,
            "recovery_required": self.recovery_required,
            "trigger": self.trigger,
            "state_reset": self.state_reset,
        }


def _load_state(path: Path) -> tuple[RuntimeWatchdogState, bool]:
    if not path.exists():
        return RuntimeWatchdogState(), False

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        state = RuntimeWatchdogState(
            tick=int(payload["tick"]),
            live_failures=int(payload["live_failures"]),
            ready_failures=int(payload["ready_failures"]),
        )
        if min(state.tick, state.live_failures, state.ready_failures) < 0:
            raise ValueError("negative watchdog state")
        return state, False
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return RuntimeWatchdogState(), True


def _write_state(path: Path, state: RuntimeWatchdogState) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError as exc:
        raise RuntimeWatchdogError("watchdog state directory permissions could not be secured") from exc

    payload = json.dumps(state.to_dict(), sort_keys=True) + "\n"
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
    except OSError as exc:
        raise RuntimeWatchdogError("watchdog state could not be persisted") from exc


def evaluate_runtime_watchdog(
    state_path: str | Path,
    probe: Callable[[ProbeKind], RuntimeProbeResult],
    *,
    failure_threshold: int = 3,
    live_every_ticks: int = 3,
) -> RuntimeWatchdogReport:
    if failure_threshold < 1:
        raise RuntimeWatchdogError("watchdog failure threshold must be positive")
    if live_every_ticks < 1:
        raise RuntimeWatchdogError("watchdog liveness cadence must be positive")

    path = Path(state_path)
    previous, state_reset = _load_state(path)
    tick = previous.tick + 1

    ready = probe("ready")
    ready_failures = 0 if ready.ok else previous.ready_failures + 1

    live: RuntimeProbeResult | None = None
    live_failures = previous.live_failures
    if tick % live_every_ticks == 0:
        live = probe("live")
        live_failures = 0 if live.ok else previous.live_failures + 1

    state = RuntimeWatchdogState(
        tick=tick,
        live_failures=live_failures,
        ready_failures=ready_failures,
    )
    _write_state(path, state)

    trigger = None
    if live_failures >= failure_threshold:
        trigger = "liveness"
    elif ready_failures >= failure_threshold:
        trigger = "readiness"

    return RuntimeWatchdogReport(
        state=state,
        live=live,
        ready=ready,
        failure_threshold=failure_threshold,
        live_every_ticks=live_every_ticks,
        recovery_required=trigger is not None,
        trigger=trigger,
        state_reset=state_reset,
    )
