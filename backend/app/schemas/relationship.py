from datetime import datetime

from pydantic import BaseModel


class RelationshipCreate(BaseModel):
    person_id: str
    status: str = "unknown"
    stage: str = "unknown"
    long_term_goal: str | None = None
    current_goal: str | None = None
    notes: str | None = None


class RelationshipUpdate(BaseModel):
    status: str | None = None
    stage: str | None = None
    long_term_goal: str | None = None
    current_goal: str | None = None
    notes: str | None = None


class RelationshipResponse(BaseModel):
    id: str
    user_id: str
    person_id: str
    status: str
    stage: str
    long_term_goal: str | None
    current_goal: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
