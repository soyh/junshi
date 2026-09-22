from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


ProviderName = Literal[
    "qwen",
    "deepseek",
    "kimi",
    "openai",
    "gemini",
    "openai_compatible",
]

ProviderValidationCode = Literal[
    "ok",
    "api_key_invalid",
    "model_invalid",
    "endpoint_invalid",
    "timeout",
    "rate_limited",
    "provider_unavailable",
    "malformed_response",
    "unknown",
]


def _validate_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("base_url must use http or https")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise ValueError("base_url must contain a host without embedded credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("base_url must not contain query or fragment components")
    return value.rstrip("/")


class LLMProviderConfigUpdate(BaseModel):
    provider: ProviderName = "openai_compatible"
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=200)
    api_key: SecretStr = Field(min_length=1, max_length=1000)
    timeout_seconds: float = Field(default=60.0, gt=0, le=300)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        return _validate_base_url(value)


class LLMProviderConfigResponse(BaseModel):
    provider: ProviderName
    base_url: str
    model: str
    timeout_seconds: float
    api_key_configured: bool


class LLMProviderProfileCreate(LLMProviderConfigUpdate):
    name: str = Field(min_length=1, max_length=80)
    activate: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("profile name cannot be empty")
        return value


class LLMProviderProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    provider: ProviderName | None = None
    base_url: str | None = Field(default=None, min_length=1, max_length=500)
    model: str | None = Field(default=None, min_length=1, max_length=200)
    api_key: SecretStr | None = Field(default=None, min_length=1, max_length=1000)
    timeout_seconds: float | None = Field(default=None, gt=0, le=300)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("profile name cannot be empty")
        return value

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_base_url(value)

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one profile field must be provided")
        return self


class LLMProviderProfileResponse(BaseModel):
    id: str
    name: str
    provider: ProviderName
    base_url: str
    model: str
    timeout_seconds: float
    api_key_configured: bool
    is_active: bool
    created_at: str
    updated_at: str


class LLMProviderValidationResult(BaseModel):
    status: Literal["ok", "error"]
    code: ProviderValidationCode
    provider: ProviderName
    model: str
    message: str
