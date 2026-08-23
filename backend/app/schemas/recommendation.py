from typing import Any

from pydantic import BaseModel


class RecommendationContextResponse(BaseModel):
    person: dict[str, Any]
    relationship: dict[str, Any]
    current_state: dict[str, Any]
    evidence: list[dict[str, Any]]
    recommendations: list[Any]
