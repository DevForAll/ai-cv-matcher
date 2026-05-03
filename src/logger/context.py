import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generator

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    return _correlation_id.get()


@contextmanager
def LogContext(operation: str = "") -> Generator[str, None, None]:
    """
    Binds a short correlation ID to every log record produced within the block.

    The ID propagates automatically through Python's contextvars — no need to
    pass it manually to each call.

    Usage:
        with LogContext("parse_cv") as cid:
            logger.info("Iniciando procesamiento", extra={"archivo": ruta.name})
    """
    cid = uuid.uuid4().hex[:8]
    token = _correlation_id.set(cid)
    try:
        yield cid
    finally:
        _correlation_id.reset(token)
