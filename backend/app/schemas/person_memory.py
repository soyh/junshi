import json
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PersonMemoryProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=1, max_length=6000)
    facts: list[str] = Field(max_length=40)
    inferences: list[str] = Field(default_factory=list, max_length=40)
    constraints: list[str] = Field(max_length=40)
    unknowns: list[str] = Field(max_length=40)
    preferences: list[str] = Field(default_factory=list,max_length=40)
    events: list[str] = Field(default_factory=list,max_length=40)
    superseded_entry_ids: list[str] = Field(default_factory=list,max_length=40)
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

    @field_validator("relationship_status", "relationship_stage")
    @classmethod
    def optional_nonblank(cls, value):
        if value is not None and not value.strip():
            raise ValueError("relationship fields cannot be blank")
        return value.strip() if value is not None else None

    @field_validator("facts", "inferences", "constraints", "unknowns", "preferences", "events")
    @classmethod
    def bounded_items(cls, values):
        if any(not v.strip() or len(v) > 500 for v in values):
            raise ValueError("invalid memory item")
        return values

    @model_validator(mode='after')
    def compact_summary(self):
        summary = self.model_dump(include={'description','facts','inferences','constraints','unknowns','preferences','events'})
        if len(json.dumps(summary,ensure_ascii=False).encode('utf-8')) > 8192:
            raise ValueError('memory summary exceeds compact input budget')
        return self
