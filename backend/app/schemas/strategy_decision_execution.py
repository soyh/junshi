from datetime import datetime

from pydantic import BaseModel, Field


class StrategyDecisionExecutionCreate(BaseModel):
    executed_at: datetime | None = None
    note: str | None = Field(default=None, max_length=2000)


class StrategyDecisionExecutionResponse(BaseModel):
    id: str
    user_id: str
    person_id: str
    decision_id: str
    executed_at: str
    note: str | None
    created_at: str


class StrategyDecisionExecutionContextResponse(BaseModel):
    person: dict
    relationship: dict | None
    decisions: list[dict]
    execution_constraints: dict


class StrategyDecisionExecutionSynthesisResponse(BaseModel):
    person: dict
    relationship: dict | None
    executions: list[dict]
    pending_decision_ids: list[str]
    execution_summary: dict
