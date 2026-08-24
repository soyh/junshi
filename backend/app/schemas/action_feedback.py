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


class ActionFeedbackSummary(BaseModel):
    total_decisions: int
    decision_counts: dict[str, int]
    outcome_observed_count: int
    outcome_unknown_count: int
    outcome_counts: dict[str, int]
    latest_observed_outcome: dict[str, str | None] | None


class ActionFeedbackTrendObservation(BaseModel):
    event_at: str
    feedback_status: str
    decision_id: str
    decision: str
    decision_created_at: str
    outcome_id: str | None
    outcome: str
    outcome_created_at: str | None
    source: dict[str, str | None]


class ActionFeedbackSignal(BaseModel):
    recommendation_id: str | None
    decision_count: int
    decision_counts: dict[str, int]
    outcome_observed_count: int
    outcome_unknown_count: int
    outcome_counts: dict[str, int]
    latest_observed_outcome: dict[str, str | None] | None


class ActionFeedbackContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    feedback_constraints: dict[str, Any]
    feedback: list[ActionFeedbackResponse]
    feedback_synthesis: list[ActionFeedbackSynthesisResponse]


class ActionFeedbackSummaryResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    feedback_summary_constraints: dict[str, Any]
    summary: ActionFeedbackSummary


class ActionFeedbackTrendResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    feedback_trend_constraints: dict[str, Any]
    observations: list[ActionFeedbackTrendObservation]


class ActionFeedbackSignalResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    feedback_signal_constraints: dict[str, Any]
    signals: list[ActionFeedbackSignal]