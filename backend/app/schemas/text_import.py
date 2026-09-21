from pydantic import BaseModel, Field


class TextImportCandidate(BaseModel):
    line_number: int = Field(gt=0)
    sent_at: str
    sender_type: str
    content: str


class TextImportRequest(BaseModel):
    person_id: str
    text: str
    title: str | None = None
    auto_sort_by_sent_at: bool = False
    conversation_id: str | None = None


class TextImportResponse(BaseModel):
    conversation_id: str
    person_id: str
    message_ids: list[str]
    imported_count: int
    candidates: list[TextImportCandidate]
