import logging
import re

# Patterns ordered by specificity — most precise first
_SENSITIVE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"sk-proj-[A-Za-z0-9\-_]{20,}"), "[OPENAI_KEY_REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9\-_]{20,}"), "[OPENAI_KEY_REDACTED]"),
    (re.compile(r"AIza[A-Za-z0-9\-_]{35}"), "[GOOGLE_KEY_REDACTED]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_.=]{8,}", re.IGNORECASE), "Bearer [TOKEN_REDACTED]"),
]


class SensitiveDataFilter(logging.Filter):
    """
    Redacts API keys and bearer tokens from log messages before emission.

    Operates on the fully-formatted message so it catches keys embedded in
    f-strings, %-style formats, or str() representations of dicts.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for pattern, replacement in _SENSITIVE_PATTERNS:
            msg = pattern.sub(replacement, msg)
        record.msg = msg
        record.args = None  # message is already fully formatted
        return True


class ContextFilter(logging.Filter):
    """Injects the active correlation_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        from .context import get_correlation_id
        record.correlation_id = get_correlation_id()
        return True
