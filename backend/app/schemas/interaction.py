from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class InteractionCreate(BaseModel):
    person_id: str
    relationship_id: str | None = None
    type: str = Field(
        min_length=1,
        max_length=50,
    )
    occurred_at: datetime
    content: str | None = None


class InteractionUpdate(BaseModel):
    relationship_id: str | None = None
    type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    occurred_at: datetime | None = None
    content: str | None = None

    @model_validator(mode="after")
    def validate_explicit_nulls(self):
        if "occurred_at" in self.model_fields_set and self.occurred_at is None:
            raise ValueError("occurred_at cannot be null")
        return self


class InteractionResponse(BaseModel):
    id: str
    user_id: str
    person_id: str
    relationship_id: str | None
    type: str
    occurred_at: datetime
    content: str | None
    created_at: datetime
    updated_at: datetime
