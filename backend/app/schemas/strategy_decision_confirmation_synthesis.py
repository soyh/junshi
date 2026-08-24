from typing import Any

from pydantic import BaseModel


class StrategyDecisionConfirmationSynthesisResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    confirmation_constraints: dict[str, Any]
    confirmation_summary: dict[str, Any]
    confirmed_recommendation_ids: list[str | None]
    rejected_recommendation_ids: list[str | None]
    execution: dict[str, Any]
