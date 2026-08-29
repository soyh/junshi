from typing import Any, Protocol

from app.schemas.structured_analysis import StructuredAnalysis


class LLMProvider(Protocol):
    """Provider boundary; implementations must not access domain persistence."""

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        ...


class LLMAnalysisError(RuntimeError):
    pass


class LLMAnalysisService:
    """Converts an AnalysisContext snapshot into validated derived analysis."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def analyze(self, context: dict[str, Any]) -> StructuredAnalysis:
        result = self.provider.analyze(context)
        if not isinstance(result, dict):
            raise LLMAnalysisError("LLM provider returned a non-object result")

        try:
            return StructuredAnalysis.model_validate(result)
        except Exception as exc:
            raise LLMAnalysisError("LLM provider returned invalid structured analysis") from exc
