import sqlite3
from urllib.parse import urlsplit

from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import get_settings
from app.repositories.llm_provider_config import LLMProviderConfigRepository
from app.schemas.llm_provider_config import (
    LLMProviderConfigResponse,
    LLMProviderConfigUpdate,
)
from app.services.llm import LLMAnalysisError, LLMProvider
from app.services.openai_chat_provider import OpenAICompatibleProvider
from app.services.qwen_provider import QwenProvider


class LLMProviderConfigError(ValueError):
    pass


_PROVIDER_PROFILES: dict[str, tuple[str, bool]] = {
    "deepseek": ("DeepSeek", False),
    "kimi": ("Kimi", False),
    "openai": ("OpenAI", True),
    "gemini": ("Gemini", True),
    "openai_compatible": ("OpenAI-compatible", False),
}


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
        except (TypeError, ValueError):
            raise LLMProviderConfigError(
                "LLM provider config encryption key is invalid"
            ) from None

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
        api_key = config.api_key.get_secret_value()
        encrypted = self._fernet().encrypt(api_key.encode("utf-8")).decode("ascii")
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

    @staticmethod
    def _is_legacy_qwen_compatible_config(provider: str, base_url: str) -> bool:
        if provider != "openai_compatible":
            return False
        hostname = (urlsplit(base_url).hostname or "").lower()
        return (
            "dashscope" in hostname
            or (
                hostname.endswith(".aliyuncs.com")
                and "compatible-mode" in urlsplit(base_url).path
            )
        )

    def build_provider(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> LLMProvider:
        row = self.repository.get(conn, user_id)
        if row is None:
            return QwenProvider()

        try:
            api_key = self._fernet().decrypt(
                row["api_key_encrypted"].encode("ascii")
            ).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, ValueError):
            raise LLMProviderConfigError(
                "stored LLM provider API key cannot be decrypted"
            ) from None

        provider_name = row["provider"]
        base_url = row["base_url"]
        model = row["model"]
        timeout_seconds = float(row["timeout_seconds"])

        if provider_name == "qwen" or self._is_legacy_qwen_compatible_config(
            provider_name,
            base_url,
        ):
            return QwenProvider(
                api_key=api_key,
                base_url=base_url,
                model=model,
                timeout_seconds=timeout_seconds,
            )

        profile = _PROVIDER_PROFILES.get(provider_name)
        if profile is None:
            raise LLMProviderConfigError("unsupported LLM provider")

        label, supports_json_schema = profile
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
            provider_name=label,
            supports_json_schema=supports_json_schema,
        )

    def test_connection(self, conn: sqlite3.Connection, user_id: str) -> None:
        provider = self.build_provider(conn, user_id)
        try:
            provider.test_connection()
        except LLMAnalysisError:
            raise
        except Exception:
            raise LLMAnalysisError("LLM provider connection test failed") from None
