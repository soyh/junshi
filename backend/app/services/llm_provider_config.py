import sqlite3

from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import get_settings
from app.repositories.llm_provider_config import LLMProviderConfigRepository
from app.schemas.llm_provider_config import (
    LLMProviderConfigResponse,
    LLMProviderConfigUpdate,
)
from app.services.llm import LLMAnalysisError, LLMProvider
from app.services.qwen_provider import QwenProvider


class LLMProviderConfigError(ValueError):
    pass


class LLMProviderConfigService:
    def __init__(self, repository: LLMProviderConfigRepository | None = None):
        self.repository = repository or LLMProviderConfigRepository()

    def _fernet(self) -> Fernet:
        key = get_settings().llm_config_encryption_key
        if not key:
            raise LLMProviderConfigError(
                "LLM provider config encryption key is not configured"
            )
        try:
            return Fernet(key)
        except (TypeError, ValueError) as exc:
            raise LLMProviderConfigError(
                "LLM provider config encryption key is invalid"
            ) from exc

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> LLMProviderConfigResponse | None:
        row = self.repository.get(conn, user_id)
        if row is None:
            return None
        return LLMProviderConfigResponse(
            provider=row["provider"],
            base_url=row["base_url"],
            model=row["model"],
            timeout_seconds=float(row["timeout_seconds"]),
            api_key_configured=bool(row["api_key_encrypted"]),
        )

    def save(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        config: LLMProviderConfigUpdate,
    ) -> LLMProviderConfigResponse:
        encrypted = self._fernet().encrypt(config.api_key.encode("utf-8")).decode(
            "ascii"
        )
        self.repository.upsert(
            conn,
            user_id,
            config.provider,
            config.base_url.rstrip("/"),
            config.model,
            config.timeout_seconds,
            encrypted,
        )
        return self.get(conn, user_id)  # type: ignore[return-value]

    def delete(self, conn: sqlite3.Connection, user_id: str) -> bool:
        return self.repository.delete(conn, user_id)

    def build_provider(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> LLMProvider:
        row = self.repository.get(conn, user_id)
        if row is None:
            return QwenProvider()

        if row["provider"] != "openai_compatible":
            raise LLMProviderConfigError("unsupported LLM provider")

        try:
            api_key = self._fernet().decrypt(
                row["api_key_encrypted"].encode("ascii")
            ).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
            raise LLMProviderConfigError(
                "stored LLM provider API key cannot be decrypted"
            ) from exc

        return QwenProvider(
            api_key=api_key,
            base_url=row["base_url"],
            model=row["model"],
            timeout_seconds=float(row["timeout_seconds"]),
        )

    def test_connection(self, conn: sqlite3.Connection, user_id: str) -> None:
        provider = self.build_provider(conn, user_id)
        try:
            provider.test_connection()
        except LLMAnalysisError:
            raise
        except Exception as exc:
            raise LLMAnalysisError("LLM provider connection test failed") from exc
