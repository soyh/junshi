from typing import Literal

from pydantic import BaseModel


class MediaAttachmentResponse(BaseModel):
    id: str
    user_id: str
    person_id: str
    conversation_id: str
    message_id: str | None
    media_type: Literal["image", "video"]
    mime_type: str
    original_filename: str
    size_bytes: int
    sent_at: str | None
    analysis_status: Literal["pending", "completed", "failed"]
    analysis_text: str | None
    created_at: str
    updated_at: str


class MediaAttachmentAnalysisResponse(BaseModel):
    attachment: MediaAttachmentResponse
    evidence_message_id: str | None = None
