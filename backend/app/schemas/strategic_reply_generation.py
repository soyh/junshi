from pydantic import BaseModel, ConfigDict, Field


class StrategicReplyGeneration(BaseModel):
    """Derived reply draft with explicit recommendation and evidence provenance."""

    model_config = ConfigDict(extra="forbid")

    recommendation_ids: list[str] = Field(min_length=1)
    reply: str = Field(min_length=1)
    evidence_source_ids: list[str] = Field(min_length=1)
