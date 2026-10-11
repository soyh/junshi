from pydantic import BaseModel


class StrategyDecisionResultContextResponse(BaseModel):
    person: dict
    relationship: dict | None
    results: list[dict]
    result_constraints: dict


class StrategyDecisionResultSynthesisResponse(BaseModel):
    person: dict
    relationship: dict | None
    results: list[dict]
    actionable_decision_ids: list[str]
    result_summary: dict
