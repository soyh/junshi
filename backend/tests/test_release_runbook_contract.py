import json

import pytest

from app.config.settings import Settings
from app.core.deployment import ReleaseRunbookError, build_release_runbook
from app.deployment import main


def _production_settings(**overrides) -> Settings:
    values = {
        "app_env": "production",
        "app_debug": False,
        "host": "127.0.0.1",
        "port": 18080,
        "auth_bootstrap_enabled": False,
        "llm_config_encryption_key": "test-encryption-secret",
    }
    values.update(overrides)
    return Settings(**values)


def test_release_runbook_has_strict_order_and_schema_version():
    runbook = build_release_runbook(_production_settings())

    assert runbook.schema_version == 1
    assert runbook.sequence == [
        "online_backup",
        "release_preflight",
        "stop_current_process",
        "switch_release",
        "start_candidate_process",
        "verify_liveness",
        "verify_readiness",
    ]


def test_online_backup_must_precede_release_switch():
    runbook = build_release_runbook(_production_settings())

    assert runbook.safety_snapshot["command"] == ["python", "-m", "app.backup"]
    assert runbook.safety_snapshot["required_exit_code"] == 0
    assert runbook.safety_snapshot["must_complete_before_release_switch"] is True
    assert runbook.safety_snapshot["database_may_remain_online"] is True
    assert runbook.sequence.index("online_backup") < runbook.sequence.index("switch_release")


def test_preflight_runs_after_backup_and_before_process_stop():
    runbook = build_release_runbook(_production_settings())

    assert runbook.preflight["command"] == ["python", "-m", "app.preflight", "--json"]
    assert runbook.preflight["required_exit_code"] == 0
    assert runbook.preflight["must_run_after_online_backup"] is True
    assert runbook.sequence.index("release_preflight") < runbook.sequence.index("stop_current_process")


def test_release_switch_is_external_and_preserves_runtime_state():
    runbook = build_release_runbook(_production_settings())

    assert runbook.release_switch["execution"] == "external-platform-action"
    assert runbook.release_switch["requires_current_process_stopped"] is True
    assert runbook.release_switch["preserve_runtime_configuration"] is True
    assert runbook.release_switch["preserve_database_and_backups"] is True
    assert runbook.release_switch["shell_command"] is None


def test_process_and_probe_commands_reuse_verified_runtime_contracts():
    runbook = build_release_runbook(_production_settings())

    assert runbook.process["stop"] == {
        "signal": "SIGTERM",
        "grace_seconds": 30,
        "escalation_signal": "SIGKILL",
    }
    assert runbook.process["start"]["command"] == ["python", "-m", "app.server"]
    assert runbook.process["start"]["required_bind_scope"] == "loopback"
    assert runbook.process["start"]["port"] == 18080
    assert runbook.verification["steps"][0]["command"] == ["python", "-m", "app.probe", "live", "--json"]
    assert runbook.verification["steps"][1]["command"] == ["python", "-m", "app.probe", "ready", "--json"]


def test_database_restore_is_never_automatic():
    runbook = build_release_runbook(_production_settings())
    restore = runbook.rollback["database_restore"]

    assert runbook.rollback["automatic_database_restore"] is False
    assert restore["manual_only"] is True
    assert restore["only_if_schema_or_data_rollback_is_required"] is True
    assert restore["requires_application_fully_offline"] is True
    assert restore["requires_verified_backup"] is True
    assert restore["command_template"] == [
        "python",
        "-m",
        "app.restore",
        "--backup",
        "<verified-backup-path>",
        "--offline-confirmed",
    ]


def test_code_rollback_does_not_imply_database_rollback():
    runbook = build_release_runbook(_production_settings())

    assert runbook.rollback["code_rollback"]["execution"] == "external-platform-action"
    assert runbook.rollback["automatic_database_restore"] is False
    assert runbook.rollback["post_rollback_verification"] == [
        ["python", "-m", "app.probe", "live", "--json"],
        ["python", "-m", "app.probe", "ready", "--json"],
    ]


def test_release_runbook_rejects_non_production():
    with pytest.raises(ReleaseRunbookError, match="APP_ENV=production"):
        build_release_runbook(_production_settings(app_env="development"))


def test_release_runbook_rejects_reserved_port_8899():
    with pytest.raises(ReleaseRunbookError, match="8899"):
        build_release_runbook(_production_settings(port=8899))


def test_release_runbook_rejects_non_loopback_bind():
    with pytest.raises(ReleaseRunbookError, match="loopback"):
        build_release_runbook(_production_settings(host="0.0.0.0"))


def test_serialized_runbook_contains_no_secrets_or_database_path():
    settings = _production_settings(
        auth_bearer_token="static-auth-secret",
        dashscope_api_key="dashscope-secret",
        llm_config_encryption_key="encryption-secret",
        database_path="/very/private/database/location.sqlite3",
    )
    serialized = json.dumps(build_release_runbook(settings).to_dict(), sort_keys=True)

    assert "static-auth-secret" not in serialized
    assert "dashscope-secret" not in serialized
    assert "encryption-secret" not in serialized
    assert "/very/private/database/location.sqlite3" not in serialized
    assert "8899" not in serialized


def test_cli_json_emits_contract_without_executing_steps(monkeypatch, capsys):
    monkeypatch.setattr("app.deployment.get_settings", lambda: _production_settings())

    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["schema_version"] == 1
    assert payload["sequence"][0] == "online_backup"
    assert payload["process"]["start"]["command"] == ["python", "-m", "app.server"]
    assert payload["rollback"]["automatic_database_restore"] is False
