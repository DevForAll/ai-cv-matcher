"""
Centralized logging module for ai-cv-matcher.

Quick start
-----------
In any module::

    from logger import get_logger
    logger = get_logger(__name__)
    logger.info("Procesando CV", extra={"archivo": "cv_demo.pdf"})

Correlate a pipeline run (all logs within the block share the same cid)::

    from logger import LogContext
    with LogContext("parse_cv") as cid:
        logger.info("Iniciando", extra={"cid": cid})

Configure at startup (optional — auto-configured on first get_logger call)::

    from logger import setup_logging, LoggingConfig
    setup_logging(LoggingConfig())

Environment variables
---------------------
See LoggingConfig docstring or .env for the full list.
"""

from .config import LoggingConfig
from .context import LogContext, get_correlation_id
from .core import get_logger, setup_logging

__all__ = [
    "get_logger",
    "setup_logging",
    "LogContext",
    "get_correlation_id",
    "LoggingConfig",
]
