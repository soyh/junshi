from typing import Literal
from pydantic import BaseModel, Field


class TextImportCandidate(BaseModel):
    line_number: int = Field(gt=0)
    sent_at: str
    sender_type: str
    content: str


class TextImportRequest(BaseModel):
    person_id: str
    conversation_id: str | None = None
    text: str
    title: str | None = None
    auto_sort_by_sent_at: bool = False
    source_format: Literal["pipe", "named_chat"] = "pipe"
    self_name: str | None = None
    other_name: str | None = None
    utc_offset: str = "+08:00"


class NamedChatPreviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    utc_offset: str = "+08:00"


class TextImportResponse(BaseModel):
    conversation_id: str
    person_id: str
    message_ids: list[str]
    imported_count: int
    candidates: list[TextImportCandidate]
