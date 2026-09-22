import json
from typing import Any

import httpx

from app.schemas.strategic_reply_generation import StrategicReplyGeneration
from app.schemas.structured_analysis import StructuredAnalysis
from app.services.llm import LLMAnalysisError, LLMProvider


class OpenAIChatProvider(LLMProvider):
    """Reusable OpenAI Chat Completions transport for compatible providers."""

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        model: str,
        timeout_seconds: float,
        provider_label: str = "LLM provider",
        client: httpx.Client | None = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.provider_label = provider_label
        self._client = client

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise LLMAnalysisError(f"{self.provider_label} API key is not configured")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": self._user_prompt(context)},
            ],
            "response_format": self._structured_response_format(
                "structured_analysis",
                StructuredAnalysis.model_json_schema(),
            ),
            **self._analysis_request_options(),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self._post_structured(payload, headers)
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise LLMAnalysisError(
                    f"{self.provider_label} returned non-text structured content"
                )
            result = json.loads(content)
        except LLMAnalysisError:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            raise LLMAnalysisError(
                f"{self.provider_label} provider request failed"
            ) from None

        if not isinstance(result, dict):
            raise LLMAnalysisError(
                f"{self.provider_label} returned a non-object structured result"
            )
        return result

    def generate_strategic_reply(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.api_key:
            raise LLMAnalysisError(f"{self.provider_label} API key is not configured")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._strategic_reply_system_prompt(),
                },
                {
                    "role": "user",
                    "content": self._strategic_reply_user_prompt(context),
                },
            ],
            "response_format": self._structured_response_format(
                "strategic_reply",
                StrategicReplyGeneration.model_json_schema(),
            ),
            **self._analysis_request_options(),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self._post_structured(payload, headers)
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise LLMAnalysisError(
                    f"{self.provider_label} returned non-text strategic reply content"
                )
            result = json.loads(content)
        except LLMAnalysisError:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            raise LLMAnalysisError(
                f"{self.provider_label} strategic reply request failed"
            ) from None

        if not isinstance(result, dict):
            raise LLMAnalysisError(
                f"{self.provider_label} returned a non-object strategic reply result"
            )
        return result

    def analyze_media(
        self,
        *,
        media_type: str,
        mime_type: str,
        data_url: str,
        prompt: str,
    ) -> str:
        """Ask a vision-capable OpenAI-compatible model to describe uploaded media."""
        if not self.api_key:
            raise LLMAnalysisError(f"{self.provider_label} API key is not configured")
        if media_type not in {"image", "video"}:
            raise LLMAnalysisError(f"unsupported media type: {media_type}")

        media_part_type = "image_url" if media_type == "image" else "video_url"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are the multimodal evidence extraction layer of AI Love "
                        "Strategist. Describe only observable content in the supplied "
                        "media. For chat screenshots, transcribe visible text and "
                        "describe observable emoji, stickers, photos, or video cues. "
                        "Do not infer hidden intentions or relationship conclusions."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": media_part_type,
                            media_part_type: {"url": data_url},
                        },
                    ],
                },
            ],
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
            if not isinstance(content, str) or not content.strip():
                raise LLMAnalysisError(
                    f"{self.provider_label} returned empty media analysis"
                )
            return content.strip()
        except LLMAnalysisError:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            raise LLMAnalysisError(
                f"{self.provider_label} media analysis request failed"
            ) from None

    def test_connection(self) -> None:
        if not self.api_key:
            raise LLMAnalysisError(f"{self.provider_label} API key is not configured")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": "Reply with OK to confirm this API connection test.",
                }
            ],
            "max_tokens": 8,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self._post(payload, headers)
            response.raise_for_status()
            body = response.json()
            choices = body["choices"]
            if not isinstance(choices, list) or not choices:
                raise LLMAnalysisError(
                    f"{self.provider_label} connection test returned no choices"
                )
        except LLMAnalysisError:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            raise LLMAnalysisError(
                f"{self.provider_label} provider connection test failed"
            ) from None

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

    def _post_structured(
        self,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> httpx.Response:
        response = self._post(payload, headers)
        response_format = payload.get("response_format") or {}
        if (
            response_format.get("type") == "json_schema"
            and self._json_schema_is_unavailable(response)
        ):
            fallback_payload = dict(payload)
            fallback_payload["response_format"] = {"type": "json_object"}
            return self._post(fallback_payload, headers)
        return response

    @staticmethod
    def _json_schema_is_unavailable(response: httpx.Response) -> bool:
        if response.status_code not in {400, 404, 422}:
            return False
        try:
            text = response.text.lower()
        except Exception:
            return False
        return (
            "json_schema" in text
            or (
                "response_format" in text
                and any(
                    token in text
                    for token in (
                        "unsupported",
                        "not supported",
                        "unknown",
                        "invalid format",
                    )
                )
            )
        )

    def _structured_response_format(
        self,
        name: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        if self._supports_json_schema():
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": name,
                    "strict": True,
                    "schema": schema,
                },
            }
        return {"type": "json_object"}

    def _supports_json_schema(self) -> bool:
        return False

    def _analysis_request_options(self) -> dict[str, Any]:
        return {}

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are the analysis layer of AI Love Strategist. "
            "Analyze only the supplied AnalysisContext. Return JSON only. "
            "Do not invent facts, evidence IDs, events, intentions, or outcomes. "
            "Treat canonical evidence as the source of truth. Preserve uncertainty "
            "and unknowns. Put interpretations in inferences or hypotheses, not facts. "
            "If conversation_focus is present, treat its recent_messages as the current "
            "conversation window and its latest_human_message as the newest state. "
            "Newer current-conversation evidence takes priority over older history when "
            "they conflict. If conversation_focus.reply_target_message is present, it "
            "is the primary incoming message the next reply must answer. Produce at "
            "least one useful hypothesis whose evidence_source_ids includes that reply "
            "target ID so downstream reply generation cannot drift to old messages. "
            "If the latest human message was sent by the user, do not behave as though "
            "an older incoming message is still unanswered. "
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
            "Apply conversation_focus before older context when it is present. "
            "Do not add markdown fences or explanatory text.\n\n"
            + json.dumps(context, ensure_ascii=False, sort_keys=True, default=str)
        )

    @staticmethod
    def _strategic_reply_system_prompt() -> str:
        return (
            "You are the strategic reply drafting layer of AI Love Strategist. "
            "Return JSON only. Use only the supplied evidence-backed recommendations, "
            "canonical evidence, and unknowns. Do not invent facts, events, promises, "
            "relationship status, intentions, or evidence IDs. Produce one concise, "
            "natural message draft that the user could choose to send. Preserve "
            "uncertainty and do not imply that any recommendation was selected, "
            "approved, executed, or sent. If conversation_focus is present, prioritize "
            "its recent_messages and newest state over older context. When "
            "reply_target_message is present, answer that message directly rather than "
            "continuing an older topic. Every ID in required_evidence_source_ids must be "
            "treated as mandatory current-turn provenance, and the generated "
            "evidence_source_ids must include at least one of those IDs. "
            "The response must contain exactly these top-level fields: "
            "recommendation_ids, reply, evidence_source_ids. recommendation_ids must be "
            "a non-empty array containing only IDs from the supplied recommendations. "
            "evidence_source_ids must be a non-empty array containing only evidence IDs "
            "already cited by those supporting recommendations and present in canonical "
            "evidence."
        )

    @staticmethod
    def _strategic_reply_user_prompt(context: dict[str, Any]) -> str:
        return (
            "Draft one evidence-backed strategic reply from this context and output the "
            "required JSON object. The current conversation focus is authoritative for "
            "what needs a reply now. Do not add markdown fences or explanatory text.\n\n"
            + json.dumps(context, ensure_ascii=False, sort_keys=True, default=str)
        )


class OpenAICompatibleProvider(OpenAIChatProvider):
    """Generic adapter for a named OpenAI Chat Completions compatible service."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        provider_name: str,
        supports_json_schema: bool = False,
        client: httpx.Client | None = None,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
            provider_label=provider_name,
            client=client,
        )
        self.provider_name = provider_name
        self._strict_json_schema = supports_json_schema

    def _supports_json_schema(self) -> bool:
        return self._strict_json_schema
