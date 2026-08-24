from typing import Any

from pydantic import BaseModel


class MemoryUpdateCandidate(BaseModel):
    id: str
    status: str
    category: str
    content: dict[str, Any]
    source_decision_id: str
    source_outcome_id: str


class MemoryUpdateContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    memory_constraints: dict[str, Any]
    candidates: list[MemoryUpdateCandidate]
