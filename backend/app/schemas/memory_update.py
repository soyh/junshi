from typing import Any

from pydantic import BaseModel


class MemoryUpdateCandidate(BaseModel):
    id: str
    status: str
    category: str
    content: dict[str, Any]
    recommendation_id: str | None
    learning_source: dict[str, Any]
    source_decision_id: str
    source_outcome_id: str
    source_created_at: str | None


class MemoryUpdateContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    memory_constraints: dict[str, Any]
    candidates: list[MemoryUpdateCandidate]
