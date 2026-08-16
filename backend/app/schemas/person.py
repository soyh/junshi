from datetime import datetime

from pydantic import BaseModel, Field


class PersonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    nickname: str | None = Field(default=None, max_length=200)
    notes: str | None = None


class PersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    nickname: str | None = Field(default=None, max_length=200)
    notes: str | None = None


class PersonResponse(BaseModel):
    id: str
    user_id: str
    name: str
    nickname: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
