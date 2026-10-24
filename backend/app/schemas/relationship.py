from datetime import datetime

from typing import Literal

from pydantic import BaseModel

#: What the user wants from this relationship. Free-text goals never changed the
#: tactics; this enum does (pacing, escalation, what may be promised).
INTENTS = ("long_term", "casual", "one_night", "friendship", "unsure")
Intent = Literal["long_term", "casual", "one_night", "friendship", "unsure"]


class RelationshipCreate(BaseModel):
    person_id: str
    status: str = "unknown"
    stage: str = "unknown"
    intent: Intent = "unsure"
    long_term_goal: str | None = None
    current_goal: str | None = None
    notes: str | None = None


class RelationshipUpdate(BaseModel):
    status: str | None = None
    stage: str | None = None
    intent: Intent | None = None
    long_term_goal: str | None = None
    current_goal: str | None = None
    notes: str | None = None


class RelationshipResponse(BaseModel):
    id: str
    user_id: str
    person_id: str
    status: str
    stage: str
    intent: str = "unsure"
    long_term_goal: str | None
    current_goal: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
