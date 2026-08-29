from typing import Any

from pydantic import BaseModel


class AnalysisContextResponse(BaseModel):
    conversation: dict[str, Any]
    person: dict[str, Any]
    messages: list[dict[str, Any]]
    facts: list[Any]
    inferences: list[Any]
    unknowns: list[Any]
    recommendations: list[Any]
    learning_strategy: dict[str, Any]
    relationship_state: dict[str, Any]
