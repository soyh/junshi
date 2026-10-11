from typing import Any

from pydantic import BaseModel


class EvidenceItem(BaseModel):
    source_type: str
    source_id: str
    person_id: str
    conversation_id: str | None
    occurred_at: str
    content: str | None
    metadata: dict[str, Any]


class EvidenceResponse(BaseModel):
    conversation_id: str
    person_id: str
    evidence: list[EvidenceItem]
