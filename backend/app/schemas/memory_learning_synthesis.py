from typing import Any

from pydantic import BaseModel


class MemoryLearningProvenance(BaseModel):
    status: str
    recommendation_id: str | None
    source_decision_id: str
    source_outcome_id: str
    outcome_observed_count: int
    outcome_unknown_count: int
    outcome_counts: dict[str, int]


class MemoryLearningUpdate(BaseModel):
    id: str
    status: str
    category: str
    source_candidate_id: str
    source_decision_id: str
    source_outcome_id: str
    source_created_at: str | None
    memory: dict[str, Any]
    unknowns: list[str]
    learning_provenance: MemoryLearningProvenance


class MemoryLearningSynthesisResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    memory_constraints: dict[str, Any]
    updates: list[MemoryLearningUpdate]
