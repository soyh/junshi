from typing import Any

import httpx

from app.config.settings import get_settings
from app.core.sentinels import UNSET, _Unset
from app.services.openai_chat_provider import OpenAIChatProvider


class QwenProvider(OpenAIChatProvider):
    """Qwen adapter on Alibaba Cloud's OpenAI-compatible chat API."""

    def __init__(
        self,
        *,
        api_key: str | None | _Unset = UNSET,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        client: httpx.Client | None = None,
    ):
        settings = get_settings()
        resolved_api_key = settings.dashscope_api_key if api_key is UNSET else api_key
        resolved_base_url = (base_url or settings.qwen_base_url).rstrip("/")
        resolved_model = model or settings.qwen_model
        resolved_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.qwen_timeout_seconds
        )
        super().__init__(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            model=resolved_model,
            timeout_seconds=resolved_timeout,
            provider_label="Qwen",
            client=client,
        )

    def _supports_json_schema(self) -> bool:
        model = self.model.strip().lower()
        return model.startswith(("qwen3.7", "qwen3.8"))

    def _analysis_request_options(self) -> dict[str, Any]:
        model = self.model.strip().lower()
        if model.startswith(("qwen3.7", "qwen3.8")):
            return {"enable_thinking": False}
        return {}
