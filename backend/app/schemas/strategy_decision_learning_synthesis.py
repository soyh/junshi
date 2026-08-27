from pydantic import BaseModel


class StrategyDecisionLearningSynthesisResponse(BaseModel):
    person: dict
    relationship: dict | None
    learning_items: list[dict]
    learning_candidate_decision_ids: list[str]
    unknown_decision_ids: list[str]
    recommendation_observed_counts: dict[str, int]
    learning_summary: dict
    synthesis_constraints: dict
