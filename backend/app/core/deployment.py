from __future__ import annotations

from dataclasses import asdict, dataclass

from app.config.settings import Settings
from app.core.supervision import (
    SupervisionContractError,
    build_supervision_contract,
)


class ReleaseRunbookError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReleaseRunbook:
    schema_version: int
    sequence: list[str]
    safety_snapshot: dict[str, object]
    preflight: dict[str, object]
    release_switch: dict[str, object]
    process: dict[str, object]
    verification: dict[str, object]
    rollback: dict[str, object]
    invariants: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_release_runbook(settings: Settings) -> ReleaseRunbook:
    try:
        supervision = build_supervision_contract(settings)
    except SupervisionContractError as exc:
        raise ReleaseRunbookError(str(exc)) from exc

    return ReleaseRunbook(
        schema_version=1,
        sequence=[
            "online_backup",
            "release_preflight",
            "stop_current_process",
            "switch_release",
            "start_candidate_process",
            "verify_liveness",
            "verify_readiness",
        ],
        safety_snapshot={
            "id": "online_backup",
            "command": ["python", "-m", "app.backup"],
            "required_exit_code": 0,
            "must_complete_before_release_switch": True,
            "artifact": "verified managed backup plus manifest",
            "database_may_remain_online": True,
        },
        preflight={
            "id": "release_preflight",
            "command": list(supervision.startup_gate["command"]),
            "required_exit_code": supervision.startup_gate["required_exit_code"],
            "must_run_after_online_backup": True,
        },
        release_switch={
            "id": "switch_release",
            "execution": "external-platform-action",
            "requires_current_process_stopped": True,
            "preserve_runtime_configuration": True,
            "preserve_database_and_backups": True,
            "shell_command": None,
        },
        process={
            "stop": {
                "signal": supervision.shutdown["signal"],
                "grace_seconds": supervision.shutdown["recommended_grace_seconds"],
                "escalation_signal": supervision.shutdown["escalation_signal"],
            },
            "start": {
                "command": list(supervision.process["command"]),
                "required_bind_scope": supervision.process["bind_scope"],
                "port": supervision.process["port"],
            },
        },
        verification={
            "ordered": True,
            "steps": [
                {
                    "id": "verify_liveness",
                    "command": list(supervision.probes["liveness"]["command"]),
                    "required_exit_code": supervision.probes["liveness"]["required_exit_code"],
                },
                {
                    "id": "verify_readiness",
                    "command": list(supervision.probes["readiness"]["command"]),
                    "required_exit_code": supervision.probes["readiness"]["required_exit_code"],
                },
            ],
        },
        rollback={
            "automatic_database_restore": False,
            "code_rollback": {
                "execution": "external-platform-action",
                "required": "switch back to the previously verified release",
            },
            "database_restore": {
                "manual_only": True,
                "only_if_schema_or_data_rollback_is_required": True,
                "requires_application_fully_offline": True,
                "requires_verified_backup": True,
                "command_template": [
                    "python",
                    "-m",
                    "app.restore",
                    "--backup",
                    "<verified-backup-path>",
                    "--offline-confirmed",
                ],
            },
            "post_rollback_verification": [
                list(supervision.probes["liveness"]["command"]),
                list(supervision.probes["readiness"]["command"]),
            ],
        },
        invariants={
            "reserved_port_8899_forbidden": True,
            "commands_are_argument_vectors": True,
            "no_shell_execution": True,
            "no_automatic_database_restore": True,
            "no_forwarded_header_trust": True,
            "secrets_not_embedded": True,
        },
    )
