from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StructuredAnalysisItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_source_ids: list[str] = Field(default_factory=list)


class StructuredAnalysis(BaseModel):
    """Derived LLM interpretation; never canonical truth."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    observed_facts: list[StructuredAnalysisItem]
    inferences: list[StructuredAnalysisItem]
    unknowns: list[StructuredAnalysisItem]
    hypotheses: list[StructuredAnalysisItem]
    emotional_signals: list[StructuredAnalysisItem]
    relationship_signals: list[StructuredAnalysisItem]
    risk_signals: list[StructuredAnalysisItem]
    intent_signals: list[StructuredAnalysisItem]
    evidence_links: list[dict[str, Any]]
    analysis_constraints: list[str]
