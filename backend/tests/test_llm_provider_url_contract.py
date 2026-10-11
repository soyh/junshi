import pytest
from pydantic import ValidationError

from app.schemas.llm_provider_config import LLMProviderConfigUpdate


def make_config(base_url: str) -> LLMProviderConfigUpdate:
    return LLMProviderConfigUpdate(
        base_url=base_url,
        model="test-model",
        api_key="test-api-key",
    )


def test_provider_base_url_accepts_http_and_https():
    assert make_config("https://example.com/v1").base_url == "https://example.com/v1"
    assert make_config("http://example.com/v1/").base_url == "http://example.com/v1"


@pytest.mark.parametrize(
    "base_url",
    [
        "example.com/v1",
        "ftp://example.com/v1",
        "file:///tmp/provider",
        "https:///v1",
    ],
)
def test_provider_base_url_requires_http_or_https_host(base_url: str):
    with pytest.raises(ValidationError, match="base_url"):
        make_config(base_url)


@pytest.mark.parametrize(
    "base_url",
    [
        "https://user:password@example.com/v1",
        "https://example.com/v1?api_key=secret",
        "https://example.com/v1#secret",
    ],
)
def test_provider_base_url_rejects_embedded_credentials_query_and_fragment(base_url: str):
    with pytest.raises(ValidationError, match="base_url"):
        make_config(base_url)
