import logging
import os
import re
from logging.handlers import RotatingFileHandler

from app.config.settings import get_settings


_REDACTION_PATTERNS = (
    re.compile(
        r"(?i)(authorization[\"']?\s*[:=]\s*[\"']?\s*bearer\s+)[^\s\"',;}]+"
    ),
    re.compile(
        r"(?i)(api[_-]?key(?:_encrypted)?[\"']?\s*[:=]\s*[\"']?\s*)[^\s\"',;}]+"
    ),
    re.compile(r"(?i)(\bbearer\s+)[^\s\"',;}]+"),
)


def redact_sensitive_text(value: object) -> str:
    text = str(value)
    for pattern in _REDACTION_PATTERNS:
        text = pattern.sub(r"\1[REDACTED]", text)
    return text


class RedactingFormatter(logging.Formatter):
    """Redact provider credentials from the complete rendered log record."""

    def format(self, record: logging.LogRecord) -> str:
        return redact_sensitive_text(super().format(record))


def setup_logging() -> None:
    settings = get_settings()

    os.makedirs(settings.log_dir, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    if root_logger.handlers:
        return

    formatter = RedactingFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        os.path.join(settings.log_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
