from typing import Any

from pydantic import BaseModel


class StrategyDecisionSynthesisResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    strategy_constraints: dict[str, bool]
    decisions: list[dict[str, Any]]
    selection: dict[str, Any]
