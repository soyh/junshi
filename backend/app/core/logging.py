import logging
import os
import re
import traceback
from logging.handlers import RotatingFileHandler

from app.config.settings import get_settings


_AUTHORIZATION_PATTERN = re.compile(
    r"(?i)([\"']?authorization[\"']?\s*[:=]\s*[\"']?)[^\r\n,;\"'}\]]+"
)
_SECRET_KEY_PATTERN = re.compile(
    r"(?i)([\"']?(?:[a-z0-9_-]*api[_-]?key|"
    r"[a-z0-9_-]*encryption[_-]?key|auth[_-]?bearer[_-]?token)"
    r"[\"']?\s*[:=]\s*[\"']?)"
    r"[^\s,;\"'}\]]+"
)
_BEARER_PATTERN = re.compile(r"(?i)(\bBearer\s+)[^\s,;\"'}\]]+")


def redact_sensitive_text(value: str) -> str:
    redacted = _AUTHORIZATION_PATTERN.sub(r"\1[REDACTED]", value)
    redacted = _SECRET_KEY_PATTERN.sub(r"\1[REDACTED]", redacted)
    redacted = _BEARER_PATTERN.sub(r"\1[REDACTED]", redacted)
    return redacted


class SensitiveDataFilter(logging.Filter):
    """Redacts provider and authentication credentials from application logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_sensitive_text(record.getMessage())
        record.args = ()

        if record.exc_info:
            rendered_exception = "".join(traceback.format_exception(*record.exc_info))
            record.exc_text = redact_sensitive_text(rendered_exception).rstrip()
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = redact_sensitive_text(record.exc_text)

        if record.stack_info:
            record.stack_info = redact_sensitive_text(record.stack_info)

        return True


def _install_redaction_filter(handler: logging.Handler) -> None:
    if not any(isinstance(item, SensitiveDataFilter) for item in handler.filters):
        handler.addFilter(SensitiveDataFilter())


def setup_logging() -> None:
    settings = get_settings()

    os.makedirs(settings.log_dir, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    if root_logger.handlers:
        for handler in root_logger.handlers:
            _install_redaction_filter(handler)
        return

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    _install_redaction_filter(console_handler)

    file_handler = RotatingFileHandler(
        os.path.join(settings.log_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    _install_redaction_filter(file_handler)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
