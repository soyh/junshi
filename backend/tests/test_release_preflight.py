from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app import preflight as preflight_cli
from app.config.settings import Settings
from app.core.backup_manifest import create_managed_backup
from app.core.preflight import check_release_preflight


def _migration_dir(tmp_path: Path, versions: tuple[str, ...] = ("001", "002")) -> Path:
    directory = tmp_path / "migrations"
    directory.mkdir()
    for version in versions:
        (directory / f"{version}_migration.sql").write_text("SELECT 1;\n", encoding="utf-8")
    return directory


def _database(path: Path, applied: tuple[str, ...] = ("001", "002")) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.executemany("INSERT INTO schema_migrations(version) VALUES (?)", [(v,) for v in applied])
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO items(value) VALUES ('alpha')")


def _settings(database: Path, **overrides) -> Settings:
    values = {
        "app_env": "production",
        "app_debug": False,
        "host": "127.0.0.1",
        "port": 18080,
        "database_path": str(database),
        "log_level": "INFO",
        "auth_bootstrap_enabled": False,
        "llm_config_encryption_key": "super-secret-test-key",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def _ready_fixture(tmp_path: Path):
    database = tmp_path / "app.sqlite3"
    migrations = _migration_dir(tmp_path)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    _database(database)
    create_managed_backup(database, backup_dir / "latest.sqlite3", now=datetime.now(timezone.utc))
    return database, migrations, backup_dir


def test_release_preflight_passes_for_secure_production_and_ready_operations(tmp_path: Path):
    database, migrations, backup_dir = _ready_fixture(tmp_path)
    settings = _settings(database)

    report = check_release_preflight(
        settings,
        database_path=database,
        migration_dir=migrations,
        backup_dir=backup_dir,
    )

    assert report.ready is True
    assert report.configuration["ok"] is True
    assert report.configuration["llm_encryption_key_configured"] is True
    assert report.launcher["ok"] is True
    assert report.launcher["workers"] == 1
    assert report.launcher["reload"] is False
    assert report.launcher["proxy_headers"] is False
    assert report.launcher["server_header"] is False
    assert report.operations["ready"] is True


@pytest.mark.parametrize(
    ("overrides", "expected_error"),
    [
        ({"app_env": "development"}, "APP_ENV must be production"),
        ({"app_debug": True}, "APP_DEBUG must be false"),
        ({"auth_bootstrap_enabled": True}, "AUTH_BOOTSTRAP_ENABLED must be false"),
        ({"llm_config_encryption_key": None}, "LLM_CONFIG_ENCRYPTION_KEY must be configured"),
        ({"port": 8899}, "PORT 8899 is reserved and forbidden"),
        ({"log_level": "VERBOSE"}, "LOG_LEVEL is invalid"),
    ],
)
def test_release_preflight_rejects_unsafe_configuration(tmp_path: Path, overrides, expected_error):
    database, migrations, backup_dir = _ready_fixture(tmp_path)
    settings = _settings(database, **overrides)

    report = check_release_preflight(
        settings,
        database_path=database,
        migration_dir=migrations,
        backup_dir=backup_dir,
    )

    assert report.ready is False
    assert report.configuration["ok"] is False
    assert expected_error in report.configuration["errors"]


def test_release_preflight_rejects_public_production_bind(tmp_path: Path):
    database, migrations, backup_dir = _ready_fixture(tmp_path)
    settings = _settings(database, host="0.0.0.0")

    report = check_release_preflight(
        settings,
        database_path=database,
        migration_dir=migrations,
        backup_dir=backup_dir,
    )

    assert report.ready is False
    assert report.launcher["ok"] is False
    assert report.launcher["error"] == "secure launcher rejected runtime configuration"


def test_release_preflight_propagates_operations_not_ready_without_backup(tmp_path: Path):
    database = tmp_path / "app.sqlite3"
    migrations = _migration_dir(tmp_path)
    _database(database)
    settings = _settings(database)

    report = check_release_preflight(
        settings,
        database_path=database,
        migration_dir=migrations,
        backup_dir=tmp_path / "missing-backups",
    )

    assert report.ready is False
    assert report.configuration["ok"] is True
    assert report.launcher["ok"] is True
    assert report.operations["backup"]["ok"] is False


def test_release_preflight_cli_json_is_secret_free_and_does_not_start_server(tmp_path: Path, monkeypatch, capsys):
    database, migrations, backup_dir = _ready_fixture(tmp_path)
    settings = _settings(database, llm_config_encryption_key="never-print-this-secret")
    monkeypatch.setattr(preflight_cli, "get_settings", lambda: settings)

    code = preflight_cli.main(
        [
            "--database",
            str(database),
            "--migrations-dir",
            str(migrations),
            "--backup-dir",
            str(backup_dir),
            "--json",
        ]
    )
    output = capsys.readouterr().out.strip()
    payload = json.loads(output)

    assert code == 0
    assert payload["ready"] is True
    assert payload["configuration"]["llm_encryption_key_configured"] is True
    assert "never-print-this-secret" not in output
    assert str(tmp_path) not in output
    assert "auth_bearer_token" not in output
    assert "dashscope_api_key" not in output
