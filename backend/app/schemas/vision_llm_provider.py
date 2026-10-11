from pydantic import BaseModel

from app.schemas.llm_provider_config import ProviderName


class LLMVisionSelectionUpdate(BaseModel):
    profile_id: str


class LLMVisionSelectionResponse(BaseModel):
    profile_id: str
    name: str
    provider: ProviderName
    base_url: str
    model: str
    timeout_seconds: float
    api_key_configured: bool
