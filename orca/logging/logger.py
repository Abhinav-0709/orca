"""Structured logging with contextual trace/request ID support for ORCA."""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Context variable for tracing requests across agent workflows
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


def set_request_id(request_id: str | None) -> None:
    """Set the current request/trace ID in execution context."""
    request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    """Get the current request/trace ID from execution context."""
    return request_id_ctx.get()


class StructuredLogFormatter(logging.Formatter):
    """Formats log records as structured text or JSON containing trace metadata."""

    def __init__(self, json_output: bool = False):
        super().__init__()
        self.json_output = json_output

    def format(self, record: logging.LogRecord) -> str:
        req_id = get_request_id() or getattr(record, "request_id", "N/A")
        agent_name = getattr(record, "agent", "system")
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()

        if self.json_output:
            log_payload: dict[str, Any] = {
                "timestamp": ts,
                "level": record.levelname,
                "logger": record.name,
                "request_id": req_id,
                "agent": agent_name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_payload["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_payload)

        # Human-readable formatted string
        exc = ""
        if record.exc_info:
            exc = f"\n{self.formatException(record.exc_info)}"
        return f"[{ts}] [{record.levelname:<7}] [req:{req_id}] [{agent_name}] {record.getMessage()}{exc}"


def get_logger(name: str, agent: str = "system") -> logging.Logger:
    """Obtain or configure a logger with ORCA structured formatting.

    Args:
        name: Logger name (usually __name__).
        agent: Subsystem or agent identifier (e.g. 'commander', 'ocean').
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredLogFormatter(json_output=False))
        logger.addHandler(handler)
        logger.propagate = False

    return logger
