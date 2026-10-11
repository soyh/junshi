from typing import Any

from pydantic import BaseModel


class ActionFeedbackLearningItem(BaseModel):
    recommendation_id: str | None
    decision_count: int
    decision_counts: dict[str, int]
    outcome_observed_count: int
    outcome_unknown_count: int
    outcome_counts: dict[str, int]
    learning_status: str
    unknowns: list[str]
    source: dict[str, Any]


class ActionFeedbackLearningResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    learning_constraints: dict[str, Any]
    items: list[ActionFeedbackLearningItem]