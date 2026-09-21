import json
from typing import Any, Protocol

from pydantic import ValidationError

from app.schemas.structured_analysis import StructuredAnalysis


class LLMProvider(Protocol):
    """Provider boundary; implementations must not access domain persistence."""

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        ...

    def generate_strategic_reply(self, context: dict[str, Any]) -> dict[str, Any]:
        ...

    def test_connection(self) -> None:
        ...


class LLMAnalysisError(RuntimeError):
    pass


_ANALYSIS_ITEM_LIST_FIELDS = (
    "observed_facts",
    "inferences",
    "unknowns",
    "hypotheses",
    "emotional_signals",
    "relationship_signals",
    "risk_signals",
    "intent_signals",
)


def _normalize_structured_analysis_result(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize only lossless/empty-shape drift; never invent missing fields."""
    normalized = dict(result)

    for field in _ANALYSIS_ITEM_LIST_FIELDS:
        if field not in normalized:
            continue
        value = normalized[field]
        if value is None:
            normalized[field] = []
            continue
        if isinstance(value, dict):
            value = [value]
            normalized[field] = value
        if not isinstance(value, list):
            continue
        normalized_items = []
        for item in value:
            if not isinstance(item, dict):
                normalized_items.append(item)
                continue
            normalized_item = dict(item)
            normalized_item.setdefault("confidence", None)
            if "evidence_source_ids" in normalized_item and normalized_item["evidence_source_ids"] is None:
                normalized_item["evidence_source_ids"] = []
            normalized_item.setdefault("evidence_source_ids", [])
            normalized_item.setdefault("action", None)
            normalized_items.append(normalized_item)
        normalized[field] = normalized_items

    if "evidence_links" in normalized:
        evidence_links = normalized["evidence_links"]
        if evidence_links is None:
            normalized["evidence_links"] = []
        elif isinstance(evidence_links, dict):
            normalized["evidence_links"] = [evidence_links]

    if "analysis_constraints" in normalized:
        constraints = normalized["analysis_constraints"]
        if constraints is None:
            normalized["analysis_constraints"] = []
        elif isinstance(constraints, str):
            normalized["analysis_constraints"] = [constraints]
        elif isinstance(constraints, dict):
            normalized["analysis_constraints"] = [
                f"{key}: {json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)}"
                for key, value in constraints.items()
            ]

    return normalized


def _validation_field_paths(exc: ValidationError) -> list[str]:
    fields: list[str] = []
    for error in exc.errors(include_url=False):
        location = ".".join(str(part) for part in error.get("loc", ())) or "root"
        if location not in fields:
            fields.append(location)
        if len(fields) >= 8:
            break
    return fields


class LLMAnalysisService:
    """Converts an AnalysisContext snapshot into validated derived StructuredAnalysis."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def analyze(self, context: dict[str, Any]) -> StructuredAnalysis:
        try:
            result = self.provider.analyze(context)
        except LLMAnalysisError:
            raise
        except Exception:
            raise LLMAnalysisError("LLM provider failed") from None

        if not isinstance(result, dict):
            raise LLMAnalysisError("LLM provider returned a non-object result")

        normalized = _normalize_structured_analysis_result(result)
        try:
            return StructuredAnalysis.model_validate(normalized)
        except ValidationError as exc:
            fields = _validation_field_paths(exc)
            suffix = ",".join(fields) if fields else "unknown"
            raise LLMAnalysisError(
                f"LLM provider returned invalid structured analysis fields={suffix}"
            ) from None
        except Exception:
            raise LLMAnalysisError("LLM provider returned invalid structured analysis") from None
