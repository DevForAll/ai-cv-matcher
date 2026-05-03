import json
import logging
from datetime import datetime, timezone

_LEVEL_COLORS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",
}

# Attributes that belong to the LogRecord internals — excluded from JSON extras
_STDLIB_ATTRS = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "id", "levelname", "levelno", "lineno", "module",
    "msecs", "message", "msg", "name", "pathname", "process",
    "processName", "relativeCreated", "stack_info", "taskName",
    "thread", "threadName", "correlation_id",
})


class JSONFormatter(logging.Formatter):
    """
    Emits one JSON object per line.

    Designed for log aggregators (Datadog, CloudWatch, ELK). Any extra fields
    passed via logger.info("msg", extra={"key": "val"}) are included at the
    top level of the JSON object.
    """

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        obj: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "correlation_id": getattr(record, "correlation_id", "-"),
        }
        if record.exc_info:
            obj["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            obj["stack_info"] = self.formatStack(record.stack_info)
        for key, value in record.__dict__.items():
            if key not in _STDLIB_ATTRS and not key.startswith("_"):
                obj[key] = value
        return json.dumps(obj, ensure_ascii=False, default=str)


class DevFormatter(logging.Formatter):
    """
    Colored, human-readable formatter for local development.

    Format: YYYY-MM-DD HH:MM:SS | LEVEL    | [cid] | logger.name | message
    """

    _FMT = (
        "%(asctime)s | {color}%(levelname)-8s{reset}"
        " | [%(correlation_id)s] | %(name)s | %(message)s"
    )
    _DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        color = _LEVEL_COLORS.get(record.levelname, "")
        reset = _LEVEL_COLORS["RESET"]
        formatter = logging.Formatter(
            fmt=self._FMT.format(color=color, reset=reset),
            datefmt=self._DATE_FMT,
        )
        result = formatter.format(record)
        if record.exc_info:
            result += "\n" + self.formatException(record.exc_info)
        return result
