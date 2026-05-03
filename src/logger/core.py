import logging
import logging.handlers
from pathlib import Path

from .config import LoggingConfig
from .filters import ContextFilter, SensitiveDataFilter
from .formatters import DevFormatter, JSONFormatter

_APP_ROOT = "ai-cv-matcher"
_configured = False


def setup_logging(config: LoggingConfig | None = None) -> None:
    """
    Configures the application root logger exactly once.

    Idempotent — safe to call multiple times. Subsequent calls after the first
    are silently ignored. Call at the application entry point before importing
    any module that uses get_logger().
    """
    global _configured, _APP_ROOT
    if _configured:
        return

    if config is None:
        config = LoggingConfig()

    _APP_ROOT = config.app_name  # respects APP_NAME from .env

    root = logging.getLogger(_APP_ROOT)
    root.setLevel(config.level)
    root.propagate = False
    root.handlers.clear()

    sensitive_filter = SensitiveDataFilter()
    context_filter = ContextFilter()
    use_json = config.format == "json" or config.is_production

    # ── Console handler ──────────────────────────────────────────────────────
    console = logging.StreamHandler()
    console.setLevel(config.level)
    console.setFormatter(JSONFormatter() if use_json else DevFormatter())
    console.addFilter(sensitive_filter)
    console.addFilter(context_filter)
    root.addHandler(console)

    # ── Rotating file handler (opt-in via LOG_FILE_ENABLED=true) ────────────
    if config.file_enabled:
        log_path = Path(config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=config.file_max_bytes,
            backupCount=config.file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(config.level)
        file_handler.setFormatter(JSONFormatter())  # always JSON in files
        file_handler.addFilter(sensitive_filter)
        file_handler.addFilter(context_filter)
        root.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Returns a child logger under the ai-cv-matcher namespace.

    Accepts any of these forms:
        get_logger(__name__)               → "ai-cv-matcher.tools.cv_parser"
        get_logger("tools.cv_parser")      → "ai-cv-matcher.tools.cv_parser"
        get_logger("ai-cv-matcher.x")      → "ai-cv-matcher.x"  (passthrough)

    Auto-calls setup_logging() on first use if not already initialized.
    """
    if not _configured:
        setup_logging()

    # Strip "src." prefix when __name__ is used inside the src/ package
    if name.startswith("src."):
        name = name[len("src."):]

    if name == _APP_ROOT or name.startswith(_APP_ROOT + "."):
        return logging.getLogger(name)

    return logging.getLogger(f"{_APP_ROOT}.{name}")
