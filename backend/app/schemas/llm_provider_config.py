from typing import Literal

from pydantic import BaseModel, Field


ProviderName = Literal["openai_compatible"]


class LLMProviderConfigUpdate(BaseModel):
    provider: ProviderName = "openai_compatible"
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=200)
    api_key: str = Field(min_length=1, max_length=1000)
    timeout_seconds: float = Field(default=60.0, gt=0, le=300)


class LLMProviderConfigResponse(BaseModel):
    provider: ProviderName
    base_url: str
    model: str
    timeout_seconds: float
    api_key_configured: bool
