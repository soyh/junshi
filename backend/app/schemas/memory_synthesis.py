from typing import Any

from pydantic import BaseModel


class MemoryUpdateProposal(BaseModel):
    id: str
    status: str
    category: str
    source_candidate_id: str
    source_decision_id: str
    source_outcome_id: str
    source_created_at: str | None
    memory: dict[str, Any]
    unknowns: list[str]


class MemoryUpdateSynthesisResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    memory_constraints: dict[str, Any]
    updates: list[MemoryUpdateProposal]
