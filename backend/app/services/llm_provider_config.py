import sqlite3
from urllib.parse import urlsplit

import httpx
from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import get_settings
from app.repositories.llm_provider_config import LLMProviderConfigRepository
from app.schemas.llm_provider_config import (
    LLMProviderConfigResponse,
    LLMProviderConfigUpdate,
    LLMProviderValidationResult,
)
from app.services.llm import LLMAnalysisError, LLMProvider
from app.services.openai_chat_provider import OpenAIChatProvider, OpenAICompatibleProvider
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

    def get(self, conn: sqlite3.Connection, user_id: str) -> LLMProviderConfigResponse | None:
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

    def save(self, conn: sqlite3.Connection, user_id: str, config: LLMProviderConfigUpdate) -> LLMProviderConfigResponse:
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
        return "dashscope" in hostname or (
            hostname.endswith(".aliyuncs.com") and "compatible-mode" in urlsplit(base_url).path
        )

    def build_provider(self, conn: sqlite3.Connection, user_id: str) -> LLMProvider:
        row = self.repository.get(conn, user_id)
        if row is None:
            return QwenProvider()

        try:
            api_key = self._fernet().decrypt(row["api_key_encrypted"].encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, ValueError):
            raise LLMProviderConfigError("stored LLM provider API key cannot be decrypted") from None

        provider_name = row["provider"]
        base_url = row["base_url"]
        model = row["model"]
        timeout_seconds = float(row["timeout_seconds"])

        if provider_name == "qwen" or self._is_legacy_qwen_compatible_config(provider_name, base_url):
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

    @staticmethod
    def _validation_result(provider_name: str, model: str, code: str, message: str) -> LLMProviderValidationResult:
        return LLMProviderValidationResult(
            status="ok" if code == "ok" else "error",
            code=code,
            provider=provider_name,
            model=model,
            message=message,
        )

    @staticmethod
    def _classify_http_failure(status_code: int, response_text: str) -> tuple[str, str]:
        text = response_text.lower()
        if status_code in {401, 403}:
            return "api_key_invalid", "Provider rejected the configured API key."
        if status_code == 429:
            return "rate_limited", "Provider rate limit was reached."
        if status_code in {408, 504}:
            return "timeout", "Provider request timed out."
        if status_code >= 500:
            return "provider_unavailable", "Provider is temporarily unavailable."
        if status_code == 404:
            if "model" in text:
                return "model_invalid", "Configured model was not found by the provider."
            return "endpoint_invalid", "Configured provider endpoint was not found."
        if status_code in {400, 422} and "model" in text:
            return "model_invalid", "Configured model was rejected by the provider."
        return "unknown", "Provider rejected the connection test request."

    def test_connection(self, conn: sqlite3.Connection, user_id: str) -> LLMProviderValidationResult:
        row = self.repository.get(conn, user_id)
        provider_name = row["provider"] if row is not None else "qwen"
        provider = self.build_provider(conn, user_id)
        model = getattr(provider, "model", row["model"] if row is not None else "")

        if isinstance(provider, OpenAIChatProvider):
            if not provider.api_key:
                return self._validation_result(
                    provider_name,
                    model,
                    "api_key_invalid",
                    "Provider API key is not configured.",
                )
            payload = {
                "model": provider.model,
                "messages": [{"role": "user", "content": "Reply with OK."}],
                "max_tokens": 8,
            }
            headers = {
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
            }
            try:
                response = provider._post(payload, headers)
            except httpx.TimeoutException:
                return self._validation_result(provider_name, model, "timeout", "Provider request timed out.")
            except (httpx.ConnectError, httpx.InvalidURL):
                return self._validation_result(provider_name, model, "endpoint_invalid", "Provider endpoint could not be reached.")
            except httpx.HTTPError:
                return self._validation_result(provider_name, model, "unknown", "Provider connection test failed.")

            if not response.is_success:
                code, message = self._classify_http_failure(response.status_code, response.text)
                return self._validation_result(provider_name, model, code, message)

            try:
                body = response.json()
                choices = body["choices"]
                if not isinstance(choices, list) or not choices:
                    raise ValueError
            except (ValueError, KeyError, TypeError):
                return self._validation_result(
                    provider_name,
                    model,
                    "malformed_response",
                    "Provider returned an unexpected response shape.",
                )

            return self._validation_result(provider_name, model, "ok", "Provider connection succeeded.")

        try:
            provider.test_connection()
        except LLMAnalysisError:
            return self._validation_result(provider_name, model, "unknown", "Provider connection test failed.")
        except Exception:
            return self._validation_result(provider_name, model, "unknown", "Provider connection test failed.")
        return self._validation_result(provider_name, model, "ok", "Provider connection succeeded.")
