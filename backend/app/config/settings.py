from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Love Strategist"
    app_env: str = "development"
    app_debug: bool = True

    host: str = "127.0.0.1"
    port: int = 18080

    database_path: str = "/opt/ai-love-strategist/data/app.sqlite3"
    log_dir: str = "/opt/ai-love-strategist/logs"
    log_level: str = "INFO"

    local_user_id: str = "00000000-0000-0000-0000-000000000001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
