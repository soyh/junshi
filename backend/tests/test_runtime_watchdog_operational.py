import stat
from pathlib import Path

from app.core.runtime_probe import RuntimeProbeResult
from app.core.runtime_watchdog import evaluate_runtime_watchdog


ROOT = Path(__file__).resolve().parents[2]
SYSTEMD = ROOT / "deploy" / "systemd"


def _result(kind: str, ok: bool) -> RuntimeProbeResult:
    return RuntimeProbeResult(
        kind=kind,
        ok=ok,
        status_code=200 if ok else 503,
        error=None if ok else "test failure",
    )


def test_readiness_requires_three_consecutive_failures(tmp_path):
    state_file = tmp_path / "runtime" / "watchdog.json"

    def probe(kind):
        return _result(kind, kind == "live")

    first = evaluate_runtime_watchdog(state_file, probe)
    second = evaluate_runtime_watchdog(state_file, probe)
    third = evaluate_runtime_watchdog(state_file, probe)

    assert first.state.ready_failures == 1
    assert second.state.ready_failures == 2
    assert first.recovery_required is False
    assert second.recovery_required is False
    assert third.recovery_required is True
    assert third.trigger == "readiness"


def test_success_resets_readiness_failure_counter(tmp_path):
    state_file = tmp_path / "runtime" / "watchdog.json"
    failing = True

    def probe(kind):
        if kind == "ready":
            return _result(kind, not failing)
        return _result(kind, True)

    evaluate_runtime_watchdog(state_file, probe)
    evaluate_runtime_watchdog(state_file, probe)
    failing = False
    recovered = evaluate_runtime_watchdog(state_file, probe)

    assert recovered.state.ready_failures == 0
    assert recovered.recovery_required is False


def test_liveness_runs_every_third_tick_and_requires_three_failures(tmp_path):
    state_file = tmp_path / "runtime" / "watchdog.json"
    live_checks = 0

    def probe(kind):
        nonlocal live_checks
        if kind == "live":
            live_checks += 1
            return _result(kind, False)
        return _result(kind, True)

    reports = [evaluate_runtime_watchdog(state_file, probe) for _ in range(9)]

    assert live_checks == 3
    assert reports[1].live is None
    assert reports[2].live is not None
    assert reports[5].state.live_failures == 2
    assert reports[5].recovery_required is False
    assert reports[8].state.live_failures == 3
    assert reports[8].recovery_required is True
    assert reports[8].trigger == "liveness"


def test_watchdog_state_permissions_are_private(tmp_path):
    state_file = tmp_path / "runtime" / "watchdog.json"

    def probe(kind):
        return _result(kind, True)

    evaluate_runtime_watchdog(state_file, probe)

    assert stat.S_IMODE(state_file.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(state_file.stat().st_mode) == 0o600


def test_corrupt_state_is_reset_without_immediate_recovery(tmp_path):
    state_file = tmp_path / "runtime" / "watchdog.json"
    state_file.parent.mkdir()
    state_file.write_text("not-json", encoding="utf-8")

    def probe(kind):
        return _result(kind, True)

    report = evaluate_runtime_watchdog(state_file, probe)

    assert report.state_reset is True
    assert report.recovery_required is False
    assert report.state.ready_failures == 0


def test_systemd_watchdog_maps_supervision_probe_contract():
    service = (SYSTEMD / "ai-love-strategist-watchdog.service").read_text(encoding="utf-8")
    timer = (SYSTEMD / "ai-love-strategist-watchdog.timer").read_text(encoding="utf-8")

    assert "ExecStart=/opt/ai-love-strategist/.venv/bin/python -m app.watchdog --json" in service
    assert "OnFailure=ai-love-strategist-recovery.service" in service
    assert "UMask=0077" in service
    assert "OnBootSec=30s" in timer
    assert "OnUnitActiveSec=10s" in timer
    assert "AccuracySec=1s" in timer
    assert "Unit=ai-love-strategist-watchdog.service" in timer
    assert "WantedBy=timers.target" in timer
    assert "8899" not in service
    assert "8899" not in timer


def test_recovery_is_rate_limited_and_only_restarts_runtime_service():
    recovery = (SYSTEMD / "ai-love-strategist-recovery.service").read_text(encoding="utf-8")

    assert "StartLimitIntervalSec=300" in recovery
    assert "StartLimitBurst=3" in recovery
    assert "Type=oneshot" in recovery
    assert "ExecStart=/usr/bin/systemctl restart ai-love-strategist.service" in recovery
    assert "ExecStart=/usr/bin/rm -f /run/ai-love-strategist/watchdog.json" in recovery
    assert "app.restore" not in recovery
    assert "8899" not in recovery


def test_installer_enables_watchdog_without_activating_it():
    installer = (SYSTEMD / "install.sh").read_text(encoding="utf-8")

    assert "ai-love-strategist-watchdog.service" in installer
    assert "ai-love-strategist-watchdog.timer" in installer
    assert "ai-love-strategist-recovery.service" in installer
    assert "systemctl enable ai-love-strategist-watchdog.timer" in installer

    forbidden = (
        "systemctl start ",
        "systemctl restart ",
        "systemctl stop ",
        "systemctl enable --now",
    )
    assert all(item not in installer for item in forbidden)
