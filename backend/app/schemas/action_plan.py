from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActionPlanConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    must_be_evidence_backed: bool = True
    must_preserve_unknowns: bool = True
    requires_user_confirmation: bool = True
    must_not_auto_execute: bool = True
    must_not_change_relationship: bool = True


class ActionPlanContextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person: dict[str, Any]
    relationship: dict[str, Any] | None
    current_state: dict[str, Any]
    evidence: list[dict[str, Any]]
    facts: list[dict[str, Any]]
    inferences: list[dict[str, Any]]
    unknowns: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    action_plan: list[dict[str, Any]] = Field(default_factory=list)
    action_constraints: ActionPlanConstraints
    learning_strategy: dict[str, Any]
