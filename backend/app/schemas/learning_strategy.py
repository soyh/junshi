from typing import Any

from pydantic import BaseModel


class LearningStrategyContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    current_state: dict[str, Any]
    evidence: list[dict[str, Any]]
    facts: list[Any]
    inferences: list[Any]
    unknowns: list[Any]
    recommendations: list[Any]
    learning_inputs: dict[str, Any]
    strategy_constraints: dict[str, bool]
