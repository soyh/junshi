from pydantic import BaseModel, Field


class ActionOutcomeCreate(BaseModel):
    outcome: str = Field(pattern="^(completed|skipped|failed)$")
    note: str | None = None


class ActionOutcomeResponse(BaseModel):
    id: str
    user_id: str
    person_id: str
    decision_id: str
    outcome: str
    note: str | None
    created_at: str
