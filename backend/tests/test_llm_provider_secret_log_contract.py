import io
import logging

import pytest

from app.core import logging as app_logging
from app.core.logging import RedactingFilter, RedactingFormatter, redact_sensitive_text


@pytest.mark.parametrize(
    ("message", "secret"),
    [
        ("Authorization: Bearer secret-token", "secret-token"),
        ("headers={'Authorization': 'Bearer secret-token'}", "secret-token"),
        ("api_key=secret-token", "secret-token"),
        ("api-key: secret-token", "secret-token"),
        ("api_key_encrypted='encrypted-secret'", "encrypted-secret"),
        ("Bearer standalone-secret", "standalone-secret"),
    ],
)
def test_provider_credentials_are_redacted_from_log_text(message, secret):
    rendered = redact_sensitive_text(message)

    assert secret not in rendered
    assert "[REDACTED]" in rendered


def test_non_sensitive_log_text_is_preserved():
    message = "Provider connection test failed for configured model"

    assert redact_sensitive_text(message) == message


def test_formatter_redacts_exception_traceback():
    formatter = RedactingFormatter("%(levelname)s | %(message)s")
    logger = logging.getLogger("test-secret-log-formatter")

    try:
        raise RuntimeError("upstream Authorization: Bearer traceback-secret")
    except RuntimeError:
        record = logger.makeRecord(
            logger.name,
            logging.ERROR,
            __file__,
            1,
            "provider failed api_key=message-secret",
            (),
            None,
            exc_info=True,
        )

    rendered = formatter.format(record)

    assert "traceback-secret" not in rendered
    assert "message-secret" not in rendered
    assert rendered.count("[REDACTED]") >= 2


def test_setup_logging_protects_preconfigured_root_handler(monkeypatch, tmp_path):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    monkeypatch.setattr(
        app_logging,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {"log_dir": str(tmp_path), "log_level": "INFO"},
        )(),
    )

    try:
        root_logger.handlers = [handler]
        app_logging.setup_logging()

        assert any(isinstance(item, RedactingFilter) for item in handler.filters)

        root_logger.error(
            "request headers Authorization: Bearer existing-handler-secret"
        )
        rendered = stream.getvalue()

        assert "existing-handler-secret" not in rendered
        assert "[REDACTED]" in rendered
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)


def test_existing_handler_redacts_exception_text(monkeypatch, tmp_path):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    monkeypatch.setattr(
        app_logging,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {"log_dir": str(tmp_path), "log_level": "INFO"},
        )(),
    )

    try:
        root_logger.handlers = [handler]
        app_logging.setup_logging()

        try:
            raise RuntimeError("provider api_key=exception-secret")
        except RuntimeError:
            root_logger.exception("provider request failed")

        rendered = stream.getvalue()

        assert "exception-secret" not in rendered
        assert "[REDACTED]" in rendered
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)
