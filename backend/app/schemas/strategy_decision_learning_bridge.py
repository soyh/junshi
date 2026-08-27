from typing import Any

from pydantic import BaseModel


class StrategyDecisionLearningBridgeResponse(BaseModel):
    items: list[dict[str, Any]]
    constraints: dict[str, bool]


class StrategyDecisionLearningBridgeSynthesisResponse(BaseModel):
    learning_candidate_decision_ids: list[str]
    unknown_decision_ids: list[str]
    recommendation_observed_counts: dict[str, int]
    learning_candidate_count: int
    unknown_count: int
    constraints: dict[str, bool]
