from typing import Any

from pydantic import BaseModel


class StrategicReplyContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    current_state: dict[str, Any]
    evidence: list[dict[str, Any]]
    facts: list[Any]
    inferences: list[Any]
    unknowns: list[Any]
    recommendations: list[Any]
    reply_constraints: dict[str, Any]
    draft: str | None
    learning_strategy: dict[str, Any]
