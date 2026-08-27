from pydantic import BaseModel


class StrategyDecisionLearningInputResponse(BaseModel):
    person: dict
    relationship: dict | None
    items: list[dict]
    learning_constraints: dict
