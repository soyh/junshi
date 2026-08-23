from pydantic import BaseModel


class AnalysisPerson(BaseModel):
    id: str
    name: str
    nickname: str | None
    notes: str | None


class AnalysisConversation(BaseModel):
    id: str
    person_id: str
    relationship_id: str | None
    title: str | None
    status: str


class AnalysisMessage(BaseModel):
    id: str
    conversation_id: str
    sender_type: str
    content: str
    sent_at: str


class AnalysisContextResponse(BaseModel):
    conversation: AnalysisConversation
    person: AnalysisPerson
    messages: list[AnalysisMessage]
    facts: list[str]
    inferences: list[str]
    unknowns: list[str]
    recommendations: list[str]
