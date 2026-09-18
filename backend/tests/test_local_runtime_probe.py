from types import SimpleNamespace

import httpx
import pytest

from app import probe as probe_cli
from app.core.runtime_probe import (
    RuntimeProbeError,
    RuntimeProbeResult,
    _client_options,
    probe_runtime,
)


def _json_transport(status_code: int, payload: dict[str, object]) -> httpx.MockTransport:
    return httpx.MockTransport(
        lambda request: httpx.Response(status_code, json=payload, request=request)
    )


def test_live_probe_accepts_expected_local_contract():
    result = probe_runtime(
        "live",
        host="127.0.0.1",
        port=18080,
        transport=_json_transport(200, {"status": "ok", "check": "liveness"}),
    )

    assert result == RuntimeProbeResult("live", True, 200, None)


def test_ready_probe_accepts_expected_local_contract():
    result = probe_runtime(
        "ready",
        host="localhost",
        port=18080,
        transport=_json_transport(200, {"status": "ready"}),
    )

    assert result == RuntimeProbeResult("ready", True, 200, None)


def test_ready_probe_normalizes_503_without_exposing_response_body():
    secret = "should-never-appear"
    result = probe_runtime(
        "ready",
        host="127.0.0.1",
        port=18080,
        transport=_json_transport(503, {"status": "not_ready", "detail": secret}),
    )

    assert result == RuntimeProbeResult("ready", False, 503, "service not ready")
    assert secret not in str(result.to_dict())


def test_probe_rejects_non_loopback_host_before_request():
    with pytest.raises(RuntimeProbeError, match="loopback"):
        probe_runtime("live", host="0.0.0.0", port=18080)


def test_probe_rejects_reserved_port_8899_before_request():
    with pytest.raises(RuntimeProbeError, match="8899"):
        probe_runtime("ready", host="127.0.0.1", port=8899)


def test_probe_http_client_disables_redirects_and_environment_proxy_trust():
    options = _client_options(2.0)

    assert options["follow_redirects"] is False
    assert options["trust_env"] is False
    assert options["timeout"] == 2.0


def test_probe_does_not_follow_redirects():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(
            302,
            headers={"location": "https://example.invalid/secret"},
            request=request,
        )

    result = probe_runtime(
        "live",
        host="127.0.0.1",
        port=18080,
        transport=httpx.MockTransport(handler),
    )

    assert result == RuntimeProbeResult("live", False, 302, "unexpected probe status")
    assert len(calls) == 1


def test_probe_normalizes_connection_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sensitive network detail", request=request)

    result = probe_runtime(
        "ready",
        host="::1",
        port=18080,
        transport=httpx.MockTransport(handler),
    )

    assert result == RuntimeProbeResult("ready", False, None, "probe connection failed")
    assert "sensitive" not in str(result.to_dict())


def test_probe_rejects_invalid_success_body():
    result = probe_runtime(
        "live",
        host="127.0.0.1",
        port=18080,
        transport=_json_transport(200, {"status": "ok", "check": "wrong"}),
    )

    assert result == RuntimeProbeResult("live", False, 200, "invalid probe response")


def test_probe_cli_uses_settings_and_machine_readable_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(
        probe_cli,
        "get_settings",
        lambda: SimpleNamespace(host="127.0.0.1", port=18080),
    )
    monkeypatch.setattr(
        probe_cli,
        "probe_runtime",
        lambda kind, **kwargs: RuntimeProbeResult(kind, True, 200, None),
    )

    exit_code = probe_cli.main(["ready", "--json"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"kind": "ready"' in output
    assert '"ok": true' in output
    assert "127.0.0.1" not in output
    assert "18080" not in output


def test_probe_cli_fail_closed_for_reserved_port(monkeypatch, capsys):
    monkeypatch.setattr(
        probe_cli,
        "get_settings",
        lambda: SimpleNamespace(host="127.0.0.1", port=8899),
    )

    exit_code = probe_cli.main(["live", "--json"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert '"ok": false' in output
    assert "8899" in output
