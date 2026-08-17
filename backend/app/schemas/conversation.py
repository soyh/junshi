from pydantic import BaseModel, field_validator


VALID_CONVERSATION_STATUSES = {
    "active",
    "archived",
}


class ConversationCreate(BaseModel):
    person_id: str
    relationship_id: str | None = None
    title: str | None = None
    status: str = "active"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_CONVERSATION_STATUSES:
            raise ValueError(
                f"Invalid conversation status: {value}"
            )
        return value


class ConversationUpdate(BaseModel):
    relationship_id: str | None = None
    title: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if value not in VALID_CONVERSATION_STATUSES:
            raise ValueError(
                f"Invalid conversation status: {value}"
            )

        return value


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    person_id: str
    relationship_id: str | None
    title: str | None
    status: str
    created_at: str
    updated_at: str
