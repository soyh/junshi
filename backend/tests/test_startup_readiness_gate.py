from types import SimpleNamespace

from app import wait_ready as wait_ready_cli
from app.core.runtime_probe import RuntimeProbeResult


def _result(ok: bool) -> RuntimeProbeResult:
    return RuntimeProbeResult(
        kind="ready",
        ok=ok,
        status_code=200 if ok else None,
        error=None if ok else "probe connection failed",
    )


def test_wait_until_ready_retries_until_success():
    calls = 0

    def probe(kind, **kwargs):
        nonlocal calls
        calls += 1
        assert kind == "ready"
        return _result(calls >= 3)

    now = [0.0]

    def monotonic():
        return now[0]

    def sleep(seconds):
        now[0] += seconds

    result = wait_ready_cli.wait_until_ready(
        host="127.0.0.1",
        port=18080,
        timeout_seconds=5,
        interval_seconds=0.5,
        probe_timeout_seconds=1,
        probe=probe,
        monotonic=monotonic,
        sleep=sleep,
    )

    assert result.ok is True
    assert result.attempts == 3
    assert calls == 3


def test_wait_until_ready_times_out_without_false_success():
    def probe(kind, **kwargs):
        return _result(False)

    now = [0.0]

    def monotonic():
        return now[0]

    def sleep(seconds):
        now[0] += seconds

    result = wait_ready_cli.wait_until_ready(
        host="127.0.0.1",
        port=18080,
        timeout_seconds=1,
        interval_seconds=0.5,
        probe_timeout_seconds=1,
        probe=probe,
        monotonic=monotonic,
        sleep=sleep,
    )

    assert result.ok is False
    assert result.attempts == 3
    assert result.error == "probe connection failed"


def test_wait_ready_cli_is_machine_readable(monkeypatch, capsys):
    monkeypatch.setattr(
        wait_ready_cli,
        "get_settings",
        lambda: SimpleNamespace(host="127.0.0.1", port=18080),
    )
    monkeypatch.setattr(
        wait_ready_cli,
        "wait_until_ready",
        lambda **kwargs: wait_ready_cli.StartupReadinessResult(
            ok=True,
            attempts=2,
            elapsed_seconds=0.5,
            status_code=200,
            error=None,
        ),
    )

    exit_code = wait_ready_cli.main(["--json"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"ok": true' in output
    assert '"attempts": 2' in output
    assert "127.0.0.1" not in output
    assert "18080" not in output


def test_systemd_start_waits_for_application_readiness():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    service = (root / "deploy/systemd/ai-love-strategist.service").read_text(
        encoding="utf-8"
    )

    assert (
        "ExecStartPost=/opt/ai-love-strategist/.venv/bin/python -m app.wait_ready "
        "--timeout-seconds 30 --interval-seconds 0.5 --probe-timeout-seconds 1 --json"
        in service
    )
    assert service.index("-m app.wait_ready") < service.index("watchdog.json")
    assert "8899" not in service
