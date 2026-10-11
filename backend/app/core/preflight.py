from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from app.config.settings import Settings
from app.core.readiness import ReadinessReport, check_readiness, default_migration_dir
from app.server import _uvicorn_options


@dataclass(frozen=True)
class PreflightReport:
    ready: bool
    configuration: dict[str, object]
    launcher: dict[str, object]
    operations: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _configuration_report(settings: Settings) -> dict[str, object]:
    environment_ok = settings.app_env.strip().lower() == "production"
    debug_ok = settings.app_debug is False
    bootstrap_ok = settings.auth_bootstrap_enabled is False
    encryption_ok = bool(settings.llm_config_encryption_key and settings.llm_config_encryption_key.strip())
    reserved_port_ok = settings.port != 8899
    log_level = settings.log_level.strip().lower()
    log_level_ok = log_level in {"critical", "error", "warning", "info", "debug", "trace"}

    errors: list[str] = []
    if not environment_ok:
        errors.append("APP_ENV must be production")
    if not debug_ok:
        errors.append("APP_DEBUG must be false")
    if not bootstrap_ok:
        errors.append("AUTH_BOOTSTRAP_ENABLED must be false")
    if not encryption_ok:
        errors.append("LLM_CONFIG_ENCRYPTION_KEY must be configured")
    if not reserved_port_ok:
        errors.append("PORT 8899 is reserved and forbidden")
    if not log_level_ok:
        errors.append("LOG_LEVEL is invalid")

    return {
        "ok": not errors,
        "environment": settings.app_env.strip().lower(),
        "debug": settings.app_debug,
        "bootstrap_enabled": settings.auth_bootstrap_enabled,
        "llm_encryption_key_configured": encryption_ok,
        "port": settings.port,
        "log_level": log_level,
        "errors": errors,
    }


def _launcher_report(settings: Settings) -> dict[str, object]:
    try:
        options = _uvicorn_options(settings)
    except RuntimeError:
        return {
            "ok": False,
            "host": settings.host,
            "port": settings.port,
            "workers": None,
            "reload": None,
            "proxy_headers": None,
            "server_header": None,
            "error": "secure launcher rejected runtime configuration",
        }

    safe = (
        options.get("workers") == 1
        and options.get("reload") is False
        and options.get("proxy_headers") is False
        and options.get("forwarded_allow_ips") == ""
        and options.get("server_header") is False
    )
    return {
        "ok": safe,
        "host": str(options.get("host")),
        "port": int(options.get("port")),
        "workers": options.get("workers"),
        "reload": options.get("reload"),
        "proxy_headers": options.get("proxy_headers"),
        "server_header": options.get("server_header"),
        "error": None if safe else "launcher safety options do not match contract",
    }


def check_release_preflight(
    settings: Settings,
    *,
    database_path: str | Path | None = None,
    migration_dir: str | Path | None = None,
    backup_dir: str | Path | None = None,
    max_backup_age_hours: float = 24.0,
) -> PreflightReport:
    database = Path(database_path or settings.database_path).resolve()
    migrations = Path(migration_dir).resolve() if migration_dir else default_migration_dir()
    backups = Path(backup_dir).resolve() if backup_dir else database.parent / "backups"

    configuration = _configuration_report(settings)
    launcher = _launcher_report(settings)
    readiness: ReadinessReport = check_readiness(
        database,
        migration_dir=migrations,
        backup_dir=backups,
        max_backup_age_hours=max_backup_age_hours,
    )
    operations = readiness.to_dict()

    return PreflightReport(
        ready=bool(configuration["ok"] and launcher["ok"] and readiness.ready),
        configuration=configuration,
        launcher=launcher,
        operations=operations,
    )
