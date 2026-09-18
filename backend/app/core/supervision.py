from __future__ import annotations

from dataclasses import asdict, dataclass

from app.config.settings import Settings
from app.server import _uvicorn_options


class SupervisionContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class SupervisionContract:
    schema_version: int
    startup_gate: dict[str, object]
    process: dict[str, object]
    probes: dict[str, object]
    shutdown: dict[str, object]
    restart: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_supervision_contract(settings: Settings) -> SupervisionContract:
    if settings.app_env.lower() != "production":
        raise SupervisionContractError("supervision contract requires APP_ENV=production")
    if settings.port == 8899:
        raise SupervisionContractError("supervision contract refuses reserved port 8899")

    try:
        uvicorn_options = _uvicorn_options(settings)
    except RuntimeError as exc:
        raise SupervisionContractError(str(exc)) from exc

    if uvicorn_options["workers"] != 1:
        raise SupervisionContractError("production supervision requires one worker")
    if uvicorn_options["reload"] is not False:
        raise SupervisionContractError("production supervision requires reload disabled")
    if uvicorn_options["proxy_headers"] is not False:
        raise SupervisionContractError("production supervision requires proxy headers disabled")
    if uvicorn_options["forwarded_allow_ips"] != "":
        raise SupervisionContractError("production supervision requires no forwarded IP trust")
    if uvicorn_options["server_header"] is not False:
        raise SupervisionContractError("production supervision requires server header disabled")

    return SupervisionContract(
        schema_version=1,
        startup_gate={
            "command": ["python", "-m", "app.preflight", "--json"],
            "required_exit_code": 0,
        },
        process={
            "command": ["python", "-m", "app.server"],
            "bind_scope": "loopback",
            "port": settings.port,
            "workers": 1,
            "reload": False,
            "proxy_headers": False,
            "forwarded_allow_ips": "",
            "server_header": False,
        },
        probes={
            "liveness": {
                "command": ["python", "-m", "app.probe", "live", "--json"],
                "required_exit_code": 0,
                "recommended_interval_seconds": 30,
                "recommended_failure_threshold": 3,
            },
            "readiness": {
                "command": ["python", "-m", "app.probe", "ready", "--json"],
                "required_exit_code": 0,
                "recommended_interval_seconds": 10,
                "recommended_failure_threshold": 3,
            },
        },
        shutdown={
            "signal": "SIGTERM",
            "recommended_grace_seconds": 30,
            "escalation_signal": "SIGKILL",
        },
        restart={
            "policy": "on-failure",
            "recommended_delay_seconds": 5,
            "restart_on_clean_exit": False,
        },
    )
