from pydantic import BaseModel


class StrategyDecisionLifecycleContextResponse(BaseModel):
    person: dict
    relationship: dict | None
    lifecycle: list[dict]
    lifecycle_constraints: dict
