from typing import Any

from pydantic import BaseModel


class ActionFeedbackLearningCandidate(BaseModel):
    recommendation_id: str | None
    synthesis_status: str
    observed_outcome_count: int
    outcome_counts: dict[str, int]
    unknown_outcome_count: int
    unknowns: list[str]
    source: dict[str, Any]


class ActionFeedbackLearningSynthesisResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    synthesis_constraints: dict[str, Any]
    candidates: list[ActionFeedbackLearningCandidate]
