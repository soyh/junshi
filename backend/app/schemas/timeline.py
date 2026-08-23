from pydantic import BaseModel, Field


class TimelineEventResponse(BaseModel):
    id: str
    user_id: str
    person_id: str
    event_type: str
    occurred_at: str
    source_type: str
    source_id: str
    title: str | None = None
    content: str | None = None
    metadata: dict = Field(default_factory=dict)


class TimelineResponse(BaseModel):
    items: list[TimelineEventResponse]
    limit: int
    offset: int
    total: int
