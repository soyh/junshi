from typing import Any

from pydantic import BaseModel


class PersonProfileResponse(BaseModel):
    person: dict[str, Any]
    relationships: list[dict[str, Any]]
    statistics: dict[str, int]
    latest_interaction: dict[str, Any] | None
