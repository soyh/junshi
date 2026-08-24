from typing import Any

from pydantic import BaseModel


class ActionFeedbackResponse(BaseModel):
    decision_id: str
    recommendation_id: str | None
    decision: str
    decision_note: str | None
    decision_created_at: str
    outcome_id: str | None
    outcome: str | None
    outcome_note: str | None
    outcome_created_at: str | None


class ActionFeedbackSynthesisResponse(BaseModel):
    decision_id: str
    outcome_id: str | None
    feedback_status: str
    decision_signal: str
    outcome_signal: str
    unknowns: list[str]
    source: dict[str, str | None]


class ActionFeedbackContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    feedback_constraints: dict[str, Any]
    feedback: list[ActionFeedbackResponse]
    feedback_synthesis: list[ActionFeedbackSynthesisResponse]
