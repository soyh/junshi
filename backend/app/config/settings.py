from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _BACKEND_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "AI Love Strategist"
    app_env: str = "development"
    app_debug: bool = True

    host: str = "127.0.0.1"
    port: int = 18080

    database_path: str = "/opt/ai-love-strategist/data/app.sqlite3"
    log_dir: str = "/opt/ai-love-strategist/logs"
    log_level: str = "INFO"

    portable_backup_directory: str = "/opt/ai-love-strategist/data/recovery_exports"
    portable_backup_encryption_key: str | None = None
    portable_backup_keep: int = 7

    media_storage_directory: str = "/opt/ai-love-strategist/data/media"
    media_max_upload_bytes: int = 50 * 1024 * 1024

    local_user_id: str = "00000000-0000-0000-0000-000000000001"
    auth_bearer_token: str | None = None
    auth_bootstrap_enabled: bool = False

    dashscope_api_key: str | None = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"
    qwen_timeout_seconds: float = 60.0
    llm_config_encryption_key: str | None = None

    # Load deployment secrets deterministically instead of depending on the
    # process working directory. The backend-local file may override the
    # project-root file for installation-specific settings.
    model_config = SettingsConfigDict(
        env_file=(
            str(_PROJECT_ROOT / ".env"),
            str(_BACKEND_ROOT / ".env"),
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
