from datetime import datetime

from pydantic import BaseModel, field_validator


VALID_MESSAGE_SENDER_TYPES = {
    "user",
    "person",
    "system",
    "assistant",
}


class MessageCreate(BaseModel):
    conversation_id: str
    sender_type: str
    content: str
    sent_at: str | None = None

    @field_validator("sender_type")
    @classmethod
    def validate_sender_type(cls, value: str) -> str:
        if value not in VALID_MESSAGE_SENDER_TYPES:
            raise ValueError(
                f"Invalid message sender type: {value}"
            )
        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message content cannot be empty")
        return value


class MessageResponse(BaseModel):
    id: str
    user_id: str
    conversation_id: str
    sender_type: str
    content: str
    sent_at: str
    created_at: str
    updated_at: str
