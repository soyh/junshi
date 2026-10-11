from typing import Any

from pydantic import BaseModel


class StrategyDecisionContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    current_state: dict[str, Any]
    strategy_constraints: dict[str, bool]
    candidates: list[dict[str, Any]]
    decision_inputs: dict[str, Any]
