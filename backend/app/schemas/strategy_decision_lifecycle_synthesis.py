from pydantic import BaseModel


class StrategyDecisionLifecycleSynthesisResponse(BaseModel):
    person: dict
    relationship: dict | None
    lifecycle: list[dict]
    actionable_decision_ids: list[str]
    feedback_learning_decision_ids: list[str]
    feedback_unknown_decision_ids: list[str]
    lifecycle_summary: dict
    synthesis_constraints: dict
