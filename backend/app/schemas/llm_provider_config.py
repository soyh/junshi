from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, SecretStr, field_validator


ProviderName = Literal["openai_compatible"]


class LLMProviderConfigUpdate(BaseModel):
    provider: ProviderName = "openai_compatible"
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=200)
    api_key: SecretStr = Field(min_length=1, max_length=1000)
    timeout_seconds: float = Field(default=60.0, gt=0, le=300)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("base_url must use http or https")
        if not parsed.hostname or parsed.username is not None or parsed.password is not None:
            raise ValueError("base_url must contain a host without embedded credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("base_url must not contain query or fragment components")
        return value.rstrip("/")


class LLMProviderConfigResponse(BaseModel):
    provider: ProviderName
    base_url: str
    model: str
    timeout_seconds: float
    api_key_configured: bool
