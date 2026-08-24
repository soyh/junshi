from typing import Any

from pydantic import BaseModel


class LearningStrategySynthesisResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    strategy_constraints: dict[str, bool]
    candidates: list[dict[str, Any]]
