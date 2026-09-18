import sqlite3
from pathlib import Path

from app.core.runtime_health import RuntimeReadinessReport, check_runtime_readiness
from app.main import settings


def _write_migrations(directory: Path, versions: list[str]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for version in versions:
        (directory / f"{version}_test.sql").write_text("SELECT 1;\n", encoding="utf-8")


def _write_database(path: Path, versions: list[str]) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT)"
        )
        for version in versions:
            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, CURRENT_TIMESTAMP)",
                (version,),
            )


def test_runtime_readiness_accepts_accessible_database_with_exact_migrations(tmp_path: Path):
    database = tmp_path / "app.sqlite3"
    migrations = tmp_path / "migrations"
    _write_migrations(migrations, ["001", "002"])
    _write_database(database, ["001", "002"])

    report = check_runtime_readiness(database, migration_dir=migrations)

    assert report.ready is True
    assert report.database == {"ok": True, "error": None}
    assert report.migrations == {
        "ok": True,
        "expected_count": 2,
        "applied_count": 2,
        "error": None,
    }


def test_runtime_readiness_missing_database_fails_without_creating_file(tmp_path: Path):
    database = tmp_path / "missing.sqlite3"
    migrations = tmp_path / "migrations"
    _write_migrations(migrations, ["001"])

    report = check_runtime_readiness(database, migration_dir=migrations)

    assert report.ready is False
    assert report.database == {"ok": False, "error": "database unavailable"}
    assert report.migrations["error"] == "database unavailable before migration check"
    assert not database.exists()


def test_runtime_readiness_rejects_corrupt_database_without_details(tmp_path: Path):
    database = tmp_path / "broken.sqlite3"
    database.write_bytes(b"not-a-sqlite-database")
    migrations = tmp_path / "migrations"
    _write_migrations(migrations, ["001"])

    report = check_runtime_readiness(database, migration_dir=migrations)

    assert report.ready is False
    assert report.database == {"ok": False, "error": "database unavailable"}
    assert str(database.resolve()) not in str(report.to_dict())


def test_runtime_readiness_rejects_migration_mismatch(tmp_path: Path):
    database = tmp_path / "app.sqlite3"
    migrations = tmp_path / "migrations"
    _write_migrations(migrations, ["001", "002"])
    _write_database(database, ["001"])

    report = check_runtime_readiness(database, migration_dir=migrations)

    assert report.ready is False
    assert report.database["ok"] is True
    assert report.migrations == {
        "ok": False,
        "expected_count": 2,
        "applied_count": 1,
        "error": "applied migrations do not match migration files",
    }


def test_legacy_health_contract_remains_compatible(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.1.0",
    }


def test_liveness_does_not_invoke_runtime_readiness(client, monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("liveness must not access runtime readiness")

    monkeypatch.setattr("app.main.check_runtime_readiness", fail_if_called)

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "check": "liveness"}


def test_http_readiness_is_ready_without_managed_backup(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == {"ok": True, "error": None}
    assert body["migrations"]["ok"] is True
    assert "backup" not in body
    assert "expected_versions" not in body["migrations"]
    assert "applied_versions" not in body["migrations"]


def test_http_readiness_returns_503_with_normalized_failure(client, monkeypatch):
    report = RuntimeReadinessReport(
        ready=False,
        database={"ok": False, "error": "database unavailable"},
        migrations={
            "ok": False,
            "expected_count": 0,
            "applied_count": 0,
            "error": "database unavailable before migration check",
        },
    )
    monkeypatch.setattr("app.main.check_runtime_readiness", lambda *args, **kwargs: report)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": {"ok": False, "error": "database unavailable"},
        "migrations": {
            "ok": False,
            "expected_count": 0,
            "applied_count": 0,
            "error": "database unavailable before migration check",
        },
    }
    serialized = response.text.lower()
    assert "/opt/" not in serialized
    assert "api_key" not in serialized
    assert "authorization" not in serialized
    assert "password" not in serialized


def test_probe_cache_contract_preserves_legacy_health(client):
    legacy = client.get("/health")
    live = client.get("/health/live")
    ready = client.get("/health/ready")

    assert legacy.headers.get("cache-control") != "no-store"
    assert live.headers["cache-control"] == "no-store"
    assert ready.headers["cache-control"] == "no-store"
