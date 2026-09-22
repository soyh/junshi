import sqlite3
from urllib.parse import urlsplit

import httpx
from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import get_settings
from app.repositories.llm_provider_config import LLMProviderConfigRepository
from app.schemas.llm_provider_config import (
    LLMProviderConfigResponse,
    LLMProviderConfigUpdate,
    LLMProviderProfileCreate,
    LLMProviderProfileResponse,
    LLMProviderProfileUpdate,
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

    @staticmethod
    def _config_response(row: sqlite3.Row) -> LLMProviderConfigResponse:
        return LLMProviderConfigResponse(
            provider=row["provider"],
            base_url=row["base_url"],
            model=row["model"],
            timeout_seconds=float(row["timeout_seconds"]),
            api_key_configured=bool(row["api_key_encrypted"]),
        )

    @staticmethod
    def _profile_response(row: sqlite3.Row) -> LLMProviderProfileResponse:
        return LLMProviderProfileResponse(
            id=row["id"],
            name=row["name"],
            provider=row["provider"],
            base_url=row["base_url"],
            model=row["model"],
            timeout_seconds=float(row["timeout_seconds"]),
            api_key_configured=bool(row["api_key_encrypted"]),
            is_active=bool(row["is_active"]),
        )

    def _runtime_row(self, conn: sqlite3.Connection, user_id: str) -> sqlite3.Row | None:
        getter = getattr(self.repository, "get_active_profile", None)
        if callable(getter):
            row = getter(conn, user_id)
            if row is not None:
                return row
        return self.repository.get(conn, user_id)

    def get(self, conn: sqlite3.Connection, user_id: str) -> LLMProviderConfigResponse | None:
        row = self._runtime_row(conn, user_id)
        if row is None:
            return None
        return self._config_response(row)

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
        sync_profile = getattr(self.repository, "upsert_legacy_profile", None)
        if callable(sync_profile):
            sync_profile(
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
        deleted = self.repository.delete(conn, user_id)
        delete_profiles = getattr(self.repository, "delete_all_profiles", None)
        if callable(delete_profiles):
            delete_profiles(conn, user_id)
        return deleted

    def list_profiles(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> list[LLMProviderProfileResponse]:
        return [
            self._profile_response(row)
            for row in self.repository.list_profiles(conn, user_id)
        ]

    def create_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        payload: LLMProviderProfileCreate,
    ) -> LLMProviderProfileResponse:
        encrypted = self._fernet().encrypt(
            payload.api_key.get_secret_value().encode("utf-8")
        ).decode("ascii")
        existing = self.repository.list_profiles(conn, user_id)
        activate = payload.activate or not existing
        try:
            row = self.repository.create_profile(
                conn,
                user_id,
                payload.name,
                payload.provider,
                payload.base_url.rstrip("/"),
                payload.model,
                payload.timeout_seconds,
                encrypted,
                activate,
            )
        except sqlite3.IntegrityError as exc:
            raise LLMProviderConfigError("LLM profile name already exists") from exc
        if activate:
            self._sync_legacy_from_profile(conn, user_id, row)
        return self._profile_response(row)

    def update_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        profile_id: str,
        payload: LLMProviderProfileUpdate,
    ) -> LLMProviderProfileResponse:
        current = self.repository.get_profile(conn, user_id, profile_id)
        if current is None:
            raise LLMProviderConfigError("LLM profile not found")
        values: dict[str, object] = {}
        for field in ("name", "provider", "base_url", "model", "timeout_seconds"):
            if field in payload.model_fields_set:
                value = getattr(payload, field)
                if value is not None:
                    values[field] = value.rstrip("/") if field == "base_url" else value
        if "api_key" in payload.model_fields_set and payload.api_key is not None:
            values["api_key_encrypted"] = self._fernet().encrypt(
                payload.api_key.get_secret_value().encode("utf-8")
            ).decode("ascii")
        try:
            row = self.repository.update_profile(conn, user_id, profile_id, values)
        except sqlite3.IntegrityError as exc:
            raise LLMProviderConfigError("LLM profile name already exists") from exc
        if row is None:
            raise LLMProviderConfigError("LLM profile not found")
        if bool(row["is_active"]):
            self._sync_legacy_from_profile(conn, user_id, row)
        return self._profile_response(row)

    def activate_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        profile_id: str,
    ) -> LLMProviderProfileResponse:
        row = self.repository.activate_profile(conn, user_id, profile_id)
        if row is None:
            raise LLMProviderConfigError("LLM profile not found")
        self._sync_legacy_from_profile(conn, user_id, row)
        return self._profile_response(row)

    def delete_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        profile_id: str,
    ) -> bool:
        current = self.repository.get_profile(conn, user_id, profile_id)
        if current is None:
            raise LLMProviderConfigError("LLM profile not found")
        was_active = bool(current["is_active"])
        if not self.repository.delete_profile(conn, user_id, profile_id):
            raise LLMProviderConfigError("LLM profile not found")
        remaining = self.repository.list_profiles(conn, user_id)
        if was_active and remaining:
            replacement = self.repository.activate_profile(conn, user_id, remaining[0]["id"])
            if replacement is not None:
                self._sync_legacy_from_profile(conn, user_id, replacement)
        elif not remaining:
            self.repository.delete(conn, user_id)
        return True

    def _sync_legacy_from_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        row: sqlite3.Row,
    ) -> None:
        self.repository.upsert(
            conn,
            user_id,
            row["provider"],
            row["base_url"],
            row["model"],
            float(row["timeout_seconds"]),
            row["api_key_encrypted"],
        )

    @staticmethod
    def _is_legacy_qwen_compatible_config(provider: str, base_url: str) -> bool:
        if provider != "openai_compatible":
            return False
        hostname = (urlsplit(base_url).hostname or "").lower()
        return "dashscope" in hostname or (
            hostname.endswith(".aliyuncs.com") and "compatible-mode" in urlsplit(base_url).path
        )

    def _build_provider_from_row(self, row: sqlite3.Row) -> LLMProvider:
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
            provider_name, base_url
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

    def build_provider(self, conn: sqlite3.Connection, user_id: str) -> LLMProvider:
        row = self._runtime_row(conn, user_id)
        if row is None:
            return QwenProvider()
        return self._build_provider_from_row(row)

    @staticmethod
    def _validation_result(
        provider_name: str,
        model: str,
        code: str,
        message: str,
    ) -> LLMProviderValidationResult:
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

    def _test_provider(
        self,
        provider: LLMProvider,
        provider_name: str,
    ) -> LLMProviderValidationResult | None:
        if not isinstance(provider, OpenAIChatProvider):
            try:
                provider.test_connection()
            except LLMAnalysisError:
                raise
            except Exception:
                raise LLMAnalysisError("LLM provider connection test failed") from None
            return None

        model = provider.model
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
            return self._validation_result(
                provider_name, model, "timeout", "Provider request timed out."
            )
        except (httpx.ConnectError, httpx.InvalidURL):
            return self._validation_result(
                provider_name,
                model,
                "endpoint_invalid",
                "Provider endpoint could not be reached.",
            )
        except httpx.HTTPError:
            return self._validation_result(
                provider_name, model, "unknown", "Provider connection test failed."
            )

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

        return self._validation_result(
            provider_name, model, "ok", "Provider connection succeeded."
        )

    def test_connection(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> LLMProviderValidationResult | None:
        row = self._runtime_row(conn, user_id)
        provider = QwenProvider() if row is None else self._build_provider_from_row(row)
        provider_name = row["provider"] if row is not None else "qwen"
        return self._test_provider(provider, provider_name)

    def test_profile_connection(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        profile_id: str,
    ) -> LLMProviderValidationResult | None:
        row = self.repository.get_profile(conn, user_id, profile_id)
        if row is None:
            raise LLMProviderConfigError("LLM profile not found")
        return self._test_provider(
            self._build_provider_from_row(row),
            row["provider"],
        )
