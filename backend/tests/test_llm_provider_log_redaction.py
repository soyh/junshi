import io
import logging
import traceback
from types import SimpleNamespace

import httpx
import pytest

from app.core.logging import SensitiveDataFilter, redact_sensitive_text
from app.schemas.llm_provider_config import LLMProviderConfigUpdate
from app.services.llm import LLMAnalysisError, LLMAnalysisService
from app.services.llm_provider_config import LLMProviderConfigService
from app.services.qwen_provider import QwenProvider


def test_provider_config_masks_api_key_in_repr_and_json():
    secret = "super-secret-api-key"
    config = LLMProviderConfigUpdate(
        base_url="https://example.test/v1",
        model="test-model",
        api_key=secret,
    )

    assert secret not in repr(config)
    assert secret not in config.model_dump_json()
    assert config.api_key.get_secret_value() == secret


def test_redact_sensitive_text_masks_authorization_bearer_and_key_labels():
    text = (
        'Authorization: Bearer auth-secret, '
        'api_key="api-secret", '
        'DASHSCOPE_API_KEY=env-secret, '
        'LLM_CONFIG_ENCRYPTION_KEY=encryption-secret, '
        'standalone Bearer standalone-secret'
    )

    redacted = redact_sensitive_text(text)

    for secret in (
        "auth-secret",
        "api-secret",
        "env-secret",
        "encryption-secret",
        "standalone-secret",
    ):
        assert secret not in redacted
    assert redacted.count("[REDACTED]") >= 5


def test_logging_filter_redacts_message_arguments_and_exception_traceback():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    handler.addFilter(SensitiveDataFilter())

    logger = logging.getLogger("test.provider.secret.redaction")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.ERROR)

    message_secret = "message-secret"
    traceback_secret = "traceback-secret"

    try:
        raise RuntimeError(f"Authorization: Bearer {traceback_secret}")
    except RuntimeError:
        logger.exception("provider failed api_key=%s", message_secret)

    rendered = stream.getvalue()
    assert message_secret not in rendered
    assert traceback_secret not in rendered
    assert "[REDACTED]" in rendered
    assert "RuntimeError" in rendered


def test_qwen_provider_does_not_chain_raw_upstream_secret_exception():
    secret = "upstream-secret"

    def handler(request):
        raise httpx.ReadError(f"Authorization: Bearer {secret}")

    provider = QwenProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(LLMAnalysisError) as exc_info:
        provider.analyze({})

    exc = exc_info.value
    rendered = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    assert secret not in rendered
    assert exc.__cause__ is None


def test_llm_analysis_service_does_not_chain_arbitrary_provider_exception():
    secret = "provider-internal-secret"

    class FailingProvider:
        def analyze(self, context):
            raise RuntimeError(f"api_key={secret}")

        def test_connection(self):
            raise NotImplementedError

    with pytest.raises(LLMAnalysisError, match="LLM provider failed") as exc_info:
        LLMAnalysisService(FailingProvider()).analyze({})

    exc = exc_info.value
    rendered = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    assert secret not in rendered
    assert exc.__cause__ is None


def test_provider_config_connection_wrapper_does_not_chain_raw_exception(monkeypatch):
    secret = "connection-internal-secret"

    class FailingProvider:
        def test_connection(self):
            raise RuntimeError(f"Authorization=Bearer {secret}")

    service = LLMProviderConfigService(repository=SimpleNamespace())
    monkeypatch.setattr(
        service,
        "build_provider",
        lambda conn, user_id: FailingProvider(),
    )

    with pytest.raises(LLMAnalysisError, match="connection test failed") as exc_info:
        service.test_connection(object(), "user-a")

    exc = exc_info.value
    rendered = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    assert secret not in rendered
    assert exc.__cause__ is None
