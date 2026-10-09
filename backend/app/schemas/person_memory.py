from pydantic import BaseModel, ConfigDict, Field, field_validator


class PersonMemoryProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=1, max_length=6000)
    facts: list[str] = Field(max_length=40)
    constraints: list[str] = Field(max_length=40)
    unknowns: list[str] = Field(max_length=40)
    relationship_status: str | None = Field(default=None, max_length=80)
    relationship_stage: str | None = Field(default=None, max_length=80)
    reason: str = Field(min_length=1, max_length=1500)
    evidence_source_ids: list[str] = Field(min_length=1, max_length=64)

    @field_validator("reason", "description")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("reason cannot be blank")
        return value.strip()

    @field_validator("facts", "constraints", "unknowns")
    @classmethod
    def bounded_items(cls, values):
        if any(not v.strip() or len(v) > 500 for v in values):
            raise ValueError("invalid memory item")
        return values
