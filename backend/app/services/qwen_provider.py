import json
from typing import Any

import httpx

from app.config.settings import get_settings
from app.core.sentinels import UNSET, _Unset
from app.services.llm import LLMAnalysisError, LLMProvider


class QwenProvider(LLMProvider):
    """Provider adapter for Qwen's OpenAI-compatible chat API."""

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
        self.api_key = (
            settings.dashscope_api_key
            if api_key is UNSET
            else api_key
        )
        self.base_url = (base_url or settings.qwen_base_url).rstrip("/")
        self.model = model or settings.qwen_model
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.qwen_timeout_seconds
        )
        self._client = client

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise LLMAnalysisError("Qwen API key is not configured")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": self._user_prompt(context),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self._post(payload, headers)
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise LLMAnalysisError("Qwen returned non-text structured content")
            result = json.loads(content)
        except LLMAnalysisError:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMAnalysisError("Qwen provider request failed") from exc

        if not isinstance(result, dict):
            raise LLMAnalysisError("Qwen returned a non-object structured result")
        return result

    def _post(self, payload: dict[str, Any], headers: dict[str, str]) -> httpx.Response:
        if self._client is not None:
            return self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )

        with httpx.Client(timeout=self.timeout_seconds) as client:
            return client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are the analysis layer of AI Love Strategist. "
            "Analyze only the supplied AnalysisContext. Return JSON only. "
            "Do not invent facts, evidence IDs, events, intentions, or outcomes. "
            "Treat canonical evidence as the source of truth. Preserve uncertainty "
            "and unknowns. Put interpretations in inferences or hypotheses, not facts. "
            "The response must contain exactly these top-level fields: summary, "
            "observed_facts, inferences, unknowns, hypotheses, emotional_signals, "
            "relationship_signals, risk_signals, intent_signals, evidence_links, "
            "analysis_constraints. Each item in the first eight item lists must have "
            "content, optional confidence from 0 to 1, and evidence_source_ids. "
            "analysis_constraints must be an array of strings (list[str]), not an object "
            "or key-value map. Each constraint should be expressed as a concise string."
        )

    @staticmethod
    def _user_prompt(context: dict[str, Any]) -> str:
        return (
            "Analyze the following AnalysisContext and output the required JSON object. "
            "Do not add markdown fences or explanatory text.\n\n"
            + json.dumps(context, ensure_ascii=False, sort_keys=True, default=str)
        )