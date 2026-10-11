import json

import pytest

from app import supervision as supervision_cli
from app.config.settings import Settings
from app.core.supervision import SupervisionContractError, build_supervision_contract


def _settings(**overrides) -> Settings:
    values = {
        "app_env": "production",
        "app_debug": False,
        "host": "127.0.0.1",
        "port": 18080,
        "auth_bootstrap_enabled": False,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_supervision_contract_uses_verified_startup_and_server_commands():
    contract = build_supervision_contract(_settings()).to_dict()

    assert contract["schema_version"] == 1
    assert contract["startup_gate"] == {
        "command": ["python", "-m", "app.preflight", "--json"],
        "required_exit_code": 0,
    }
    assert contract["process"]["command"] == ["python", "-m", "app.server"]


def test_supervision_contract_preserves_secure_launcher_boundary():
    process = build_supervision_contract(_settings()).to_dict()["process"]

    assert process["bind_scope"] == "loopback"
    assert process["port"] == 18080
    assert process["workers"] == 1
    assert process["reload"] is False
    assert process["proxy_headers"] is False
    assert process["forwarded_allow_ips"] == ""
    assert process["server_header"] is False


def test_supervision_contract_uses_local_probe_cli_for_live_and_ready():
    probes = build_supervision_contract(_settings()).to_dict()["probes"]

    assert probes["liveness"]["command"] == [
        "python",
        "-m",
        "app.probe",
        "live",
        "--json",
    ]
    assert probes["readiness"]["command"] == [
        "python",
        "-m",
        "app.probe",
        "ready",
        "--json",
    ]
    assert probes["liveness"]["required_exit_code"] == 0
    assert probes["readiness"]["required_exit_code"] == 0


def test_supervision_contract_defines_graceful_shutdown_and_restart_policy():
    contract = build_supervision_contract(_settings()).to_dict()

    assert contract["shutdown"] == {
        "signal": "SIGTERM",
        "recommended_grace_seconds": 30,
        "escalation_signal": "SIGKILL",
    }
    assert contract["restart"] == {
        "policy": "on-failure",
        "recommended_delay_seconds": 5,
        "restart_on_clean_exit": False,
    }


def test_supervision_contract_rejects_non_production_environment():
    with pytest.raises(SupervisionContractError, match="APP_ENV=production"):
        build_supervision_contract(_settings(app_env="development"))


def test_supervision_contract_rejects_public_bind():
    with pytest.raises(SupervisionContractError, match="loopback"):
        build_supervision_contract(_settings(host="0.0.0.0"))


def test_supervision_contract_rejects_reserved_port_8899():
    with pytest.raises(SupervisionContractError, match="8899"):
        build_supervision_contract(_settings(port=8899))


def test_supervision_contract_never_serializes_credentials_or_database_path():
    settings = _settings(
        database_path="/secret/customer/app.sqlite3",
        auth_bearer_token="auth-secret-value",
        dashscope_api_key="dashscope-secret-value",
        llm_config_encryption_key="encryption-secret-value",
    )

    serialized = json.dumps(build_supervision_contract(settings).to_dict(), sort_keys=True)

    assert "/secret/customer/app.sqlite3" not in serialized
    assert "auth-secret-value" not in serialized
    assert "dashscope-secret-value" not in serialized
    assert "encryption-secret-value" not in serialized


def test_supervision_commands_are_argument_vectors_not_shell_strings():
    contract = build_supervision_contract(_settings()).to_dict()

    commands = [
        contract["startup_gate"]["command"],
        contract["process"]["command"],
        contract["probes"]["liveness"]["command"],
        contract["probes"]["readiness"]["command"],
    ]
    assert all(isinstance(command, list) for command in commands)
    assert all("sh" not in command[:1] and "bash" not in command[:1] for command in commands)


def test_supervision_cli_emits_machine_readable_contract(monkeypatch, capsys):
    monkeypatch.setattr(supervision_cli, "get_settings", lambda: _settings())

    exit_code = supervision_cli.main(["--json"])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["schema_version"] == 1
    assert payload["process"]["command"] == ["python", "-m", "app.server"]
    assert payload["process"]["port"] == 18080


def test_supervision_cli_fails_closed_for_invalid_runtime(monkeypatch, capsys):
    monkeypatch.setattr(
        supervision_cli,
        "get_settings",
        lambda: _settings(host="0.0.0.0"),
    )

    exit_code = supervision_cli.main(["--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["ok"] is False
    assert "loopback" in payload["error"]
