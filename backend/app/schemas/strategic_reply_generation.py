import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrategicReplyGeneration(BaseModel):
    """Derived reply draft with explicit recommendation and evidence provenance."""

    model_config = ConfigDict(extra="forbid")

    recommendation_ids: list[str] = Field(min_length=1)
    reply: str = Field(min_length=1)
    evidence_source_ids: list[str] = Field(min_length=1)

    @field_validator("reply")
    @classmethod
    def require_visible_reply(cls, value: str) -> str:
        value = value.strip()
        if not any(not char.isspace() and unicodedata.category(char) not in {"Cf", "Cc"}
                   for char in value):
            raise ValueError("reply must contain visible text")
        return value
