from typing import Any

from pydantic import BaseModel, Field


class ActionDecisionCreate(BaseModel):
    recommendation_id: str | None = None
    decision: str = Field(pattern="^(confirmed|rejected)$")
    note: str | None = None


class ActionDecisionResponse(BaseModel):
    id: str
    user_id: str
    person_id: str
    recommendation_id: str | None
    decision: str
    note: str | None
    created_at: str


class ActionDecisionContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    action_plan: list[dict[str, Any]]
    action_constraints: dict[str, Any]
    decisions: list[ActionDecisionResponse]
