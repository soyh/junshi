from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


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


class MessageUpdate(BaseModel):
    sender_type: str | None = None
    content: str | None = None
    sent_at: str | None = None

    @field_validator("sender_type")
    @classmethod
    def validate_sender_type(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_MESSAGE_SENDER_TYPES:
            raise ValueError(
                f"Invalid message sender type: {value}"
            )
        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Message content cannot be empty")
        return value

    @field_validator("sent_at")
    @classmethod
    def validate_sent_at(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("sent_at must be an ISO 8601 timestamp") from None
        return value

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one message field must be provided")
        return self


class MessageHistoryQuery(BaseModel):
    from_time: str | None = None
    to_time: str | None = None
    before: str | None = None
    limit: int = Field(default=100, ge=1, le=500)


class MessageResponse(BaseModel):
    id: str
    user_id: str
    conversation_id: str
    sender_type: str
    content: str
    sent_at: str
    created_at: str
    updated_at: str
