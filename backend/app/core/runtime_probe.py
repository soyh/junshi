from __future__ import annotations

from dataclasses import asdict, dataclass
from ipaddress import ip_address
from typing import Literal

import httpx

ProbeKind = Literal["live", "ready"]


class RuntimeProbeError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeProbeResult:
    kind: ProbeKind
    ok: bool
    status_code: int | None
    error: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalize_loopback_host(host: str) -> str:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return normalized

    try:
        address = ip_address(normalized)
    except ValueError as exc:
        raise RuntimeProbeError("runtime probe requires a loopback host") from exc

    if not address.is_loopback:
        raise RuntimeProbeError("runtime probe requires a loopback host")
    return normalized


def _probe_url(kind: ProbeKind, host: str, port: int) -> str:
    normalized_host = _normalize_loopback_host(host)
    if port == 8899:
        raise RuntimeProbeError("runtime probe refuses reserved port 8899")
    if port < 1 or port > 65535:
        raise RuntimeProbeError("runtime probe port is invalid")

    rendered_host = f"[{normalized_host}]" if ":" in normalized_host else normalized_host
    return f"http://{rendered_host}:{port}/health/{kind}"


def _client_options(timeout_seconds: float) -> dict[str, object]:
    if timeout_seconds <= 0:
        raise RuntimeProbeError("runtime probe timeout must be positive")
    return {
        "timeout": timeout_seconds,
        "follow_redirects": False,
        "trust_env": False,
    }


def probe_runtime(
    kind: ProbeKind,
    *,
    host: str,
    port: int,
    timeout_seconds: float = 2.0,
    transport: httpx.BaseTransport | None = None,
) -> RuntimeProbeResult:
    if kind not in {"live", "ready"}:
        raise RuntimeProbeError("runtime probe kind is invalid")

    url = _probe_url(kind, host, port)
    options = _client_options(timeout_seconds)
    if transport is not None:
        options["transport"] = transport

    try:
        with httpx.Client(**options) as client:
            response = client.get(url)
    except httpx.HTTPError:
        return RuntimeProbeResult(
            kind=kind,
            ok=False,
            status_code=None,
            error="probe connection failed",
        )

    if kind == "ready" and response.status_code == 503:
        return RuntimeProbeResult(
            kind=kind,
            ok=False,
            status_code=503,
            error="service not ready",
        )

    if response.status_code != 200:
        return RuntimeProbeResult(
            kind=kind,
            ok=False,
            status_code=response.status_code,
            error="unexpected probe status",
        )

    try:
        payload = response.json()
    except ValueError:
        return RuntimeProbeResult(
            kind=kind,
            ok=False,
            status_code=200,
            error="invalid probe response",
        )

    expected_status = "ok" if kind == "live" else "ready"
    if not isinstance(payload, dict) or payload.get("status") != expected_status:
        return RuntimeProbeResult(
            kind=kind,
            ok=False,
            status_code=200,
            error="invalid probe response",
        )
    if kind == "live" and payload.get("check") != "liveness":
        return RuntimeProbeResult(
            kind=kind,
            ok=False,
            status_code=200,
            error="invalid probe response",
        )

    return RuntimeProbeResult(
        kind=kind,
        ok=True,
        status_code=200,
        error=None,
    )
