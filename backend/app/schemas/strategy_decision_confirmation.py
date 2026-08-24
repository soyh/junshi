from typing import Any

from pydantic import BaseModel

from app.schemas.action_decision import ActionDecisionCreate, ActionDecisionResponse


class StrategyDecisionConfirmationResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    decisions: list[dict[str, Any]]
    confirmation_constraints: dict[str, Any]


class StrategyDecisionConfirmationCreate(ActionDecisionCreate):
    pass


class StrategyDecisionConfirmationCreatedResponse(ActionDecisionResponse):
    pass
