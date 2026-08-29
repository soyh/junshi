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
    observed_facts: list[StructuredAnalysisItem] = Field(default_factory=list)
    inferences: list[StructuredAnalysisItem] = Field(default_factory=list)
    unknowns: list[StructuredAnalysisItem] = Field(default_factory=list)
    hypotheses: list[StructuredAnalysisItem] = Field(default_factory=list)
    emotional_signals: list[StructuredAnalysisItem] = Field(default_factory=list)
    relationship_signals: list[StructuredAnalysisItem] = Field(default_factory=list)
    risk_signals: list[StructuredAnalysisItem] = Field(default_factory=list)
    intent_signals: list[StructuredAnalysisItem] = Field(default_factory=list)
    evidence_links: list[dict[str, Any]] = Field(default_factory=list)
    analysis_constraints: list[str] = Field(default_factory=list)
