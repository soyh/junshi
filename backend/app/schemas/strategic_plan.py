"""Strategic plan: the "marshal" layer that decides what to do before wording."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlanOption(BaseModel):
    """One tactic the marshal offers, optionally a "do not send" option."""

    model_config = ConfigDict(extra="ignore")

    tactic: str = Field(min_length=1, max_length=40)
    why: str = Field(min_length=1, max_length=300)
    line: str = Field(default="", max_length=400)
    send: bool = True
    source: str = Field(default="", max_length=200)
    risk: str = Field(default="", max_length=120)
    evidence_source_ids: list[str] = Field(default_factory=list)

    @field_validator("tactic", "why", "source", "risk", "line")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class StrategicPlan(BaseModel):
    """A read of the situation plus a small set of ranked tactics."""

    model_config = ConfigDict(extra="ignore")

    read: str = Field(min_length=1, max_length=400)
    signal: Literal["green", "yellow", "red"] = "yellow"
    stage: str = Field(default="", max_length=60)
    goal_this_turn: str = Field(default="", max_length=160)
    options: list[PlanOption] = Field(default_factory=list, max_length=4)
    avoid: list[str] = Field(default_factory=list, max_length=6)
    confidence: float = Field(default=0.5, ge=0, le=1)

    @field_validator("avoid")
    @classmethod
    def trim_avoid(cls, value: list[str]) -> list[str]:
        return [item.strip()[:160] for item in value if isinstance(item, str) and item.strip()]

    def sendable(self) -> list[PlanOption]:
        return [option for option in self.options if option.send and option.line.strip()]
