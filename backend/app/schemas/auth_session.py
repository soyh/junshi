from pydantic import BaseModel


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str


class AuthSessionSummary(BaseModel):
    id: str
    expires_at: str
    created_at: str
    current: bool
