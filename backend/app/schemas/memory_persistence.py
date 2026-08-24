from typing import Any

from pydantic import BaseModel


class MemoryPersistResponse(BaseModel):
    id: str
    status: str
    category: str
    person_id: str
    source_candidate_id: str
    source_decision_id: str
    source_outcome_id: str
    memory: dict[str, Any]
    created_at: str
