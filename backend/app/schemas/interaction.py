from datetime import datetime

from pydantic import BaseModel, Field


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
