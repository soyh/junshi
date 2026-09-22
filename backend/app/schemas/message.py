from pydantic import BaseModel, field_validator, model_validator


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
            raise ValueError(f"Invalid message sender type: {value}")
        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Message content cannot be empty")
        return value

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one message field must be supplied")
        return self


class MessageResponse(BaseModel):
    id: str
    user_id: str
    conversation_id: str
    sender_type: str
    content: str
    sent_at: str
    created_at: str
    updated_at: str
