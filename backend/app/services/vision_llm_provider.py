import sqlite3

import httpx

from app.schemas.llm_provider_config import LLMProviderValidationResult
from app.schemas.vision_llm_provider import LLMVisionSelectionResponse
from app.services.llm import LLMProvider
from app.services.llm_provider_config import (
    LLMProviderConfigError,
    LLMProviderConfigService,
)
from app.services.openai_chat_provider import OpenAIChatProvider


_TEST_IMAGE_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Z2S8AAAAASUVORK5CYII="
)


class LLMVisionProviderService:
    """Resolve the optional vision profile without changing the primary model.

    When no dedicated vision profile is selected, media analysis intentionally
    falls back to the existing primary provider so TEST-177/178 behavior stays
    backward compatible.
    """

    def __init__(
        self,
        provider_config_service: LLMProviderConfigService | None = None,
    ):
        self.provider_config_service = (
            provider_config_service or LLMProviderConfigService()
        )

    @staticmethod
    def _selection_response(row: sqlite3.Row) -> LLMVisionSelectionResponse:
        return LLMVisionSelectionResponse(
            profile_id=row["id"],
            name=row["name"],
            provider=row["provider"],
            base_url=row["base_url"],
            model=row["model"],
            timeout_seconds=float(row["timeout_seconds"]),
            api_key_configured=bool(row["api_key_encrypted"]),
        )

    @staticmethod
    def _selected_row(
        conn: sqlite3.Connection,
        user_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT profile.*
            FROM user_llm_vision_profile_selection selection
            JOIN user_llm_provider_profiles profile
              ON profile.id = selection.profile_id
             AND profile.user_id = selection.user_id
            WHERE selection.user_id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> LLMVisionSelectionResponse | None:
        row = self._selected_row(conn, user_id)
        if row is None:
            return None
        return self._selection_response(row)

    def select(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        profile_id: str,
    ) -> LLMVisionSelectionResponse:
        profile = self.provider_config_service.repository.get_profile(
            conn,
            user_id,
            profile_id,
        )
        if profile is None:
            raise LLMProviderConfigError("LLM profile not found")

        conn.execute(
            """
            INSERT INTO user_llm_vision_profile_selection (
                user_id,
                profile_id
            ) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                profile_id = excluded.profile_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, profile_id),
        )
        return self._selection_response(profile)

    @staticmethod
    def clear(
        conn: sqlite3.Connection,
        user_id: str,
    ) -> bool:
        cursor = conn.execute(
            "DELETE FROM user_llm_vision_profile_selection WHERE user_id = ?",
            (user_id,),
        )
        return cursor.rowcount > 0

    def build_provider(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> LLMProvider:
        row = self._selected_row(conn, user_id)
        if row is None:
            return self.provider_config_service.build_provider(conn, user_id)

        # Reuse the exact provider materialization/decryption path already used
        # by the primary model. The only difference here is profile selection.
        return self.provider_config_service._provider_from_row(row)

    def test_vision_capability(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> LLMProviderValidationResult:
        row = self._selected_row(conn, user_id)
        if row is None:
            row = self.provider_config_service._selected_row(conn, user_id)

        provider = self.build_provider(conn, user_id)
        provider_name = row["provider"] if row is not None else "qwen"
        model = provider.model if isinstance(provider, OpenAIChatProvider) else ""

        if not isinstance(provider, OpenAIChatProvider):
            return self.provider_config_service._validation_result(
                provider_name,
                model,
                "unknown",
                "Configured provider does not support vision requests.",
            )

        if not provider.api_key:
            return self.provider_config_service._validation_result(
                provider_name,
                provider.model,
                "api_key_invalid",
                "Provider API key is not configured.",
            )

        payload = {
            "model": provider.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Reply with OK if you can process this image.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": _TEST_IMAGE_DATA_URL,
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 8,
        }
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = provider._post(payload, headers)
        except httpx.TimeoutException:
            return self.provider_config_service._validation_result(
                provider_name,
                provider.model,
                "timeout",
                "Vision provider request timed out.",
            )
        except (httpx.ConnectError, httpx.InvalidURL):
            return self.provider_config_service._validation_result(
                provider_name,
                provider.model,
                "endpoint_invalid",
                "Vision provider endpoint could not be reached.",
            )
        except httpx.HTTPError:
            return self.provider_config_service._validation_result(
                provider_name,
                provider.model,
                "unknown",
                "Vision provider connection test failed.",
            )

        if not response.is_success:
            code, message = self.provider_config_service._classify_http_failure(
                response.status_code,
                response.text,
            )
            return self.provider_config_service._validation_result(
                provider_name,
                provider.model,
                code,
                message,
            )

        try:
            body = response.json()
            choices = body["choices"]
            if not isinstance(choices, list) or not choices:
                raise ValueError
        except (ValueError, KeyError, TypeError):
            return self.provider_config_service._validation_result(
                provider_name,
                provider.model,
                "malformed_response",
                "Vision provider returned an unexpected response shape.",
            )

        return self.provider_config_service._validation_result(
            provider_name,
            provider.model,
            "ok",
            "Vision provider accepted an image request.",
        )
