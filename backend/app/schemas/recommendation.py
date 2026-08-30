from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Recommendation(BaseModel):
    """Evidence-backed decision recommendation; never canonical truth or execution."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    evidence_source_ids: list[str] = Field(min_length=1)
    action: str | None = None
    reply: str | None = None
    priority: str | None = None
    time_horizon: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class RecommendationContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    current_state: dict[str, Any]
    evidence: list[dict[str, Any]]
    facts: list[Any]
    inferences: list[Any]
    unknowns: list[Any]
    recommendations: list[Recommendation]
    learning_strategy: dict[str, Any]
