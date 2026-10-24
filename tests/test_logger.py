"""Unit tests for ORCA logging and trace ID propagation."""

import logging
from orca.logging.logger import StructuredLogFormatter, get_logger, get_request_id, set_request_id


def test_request_id_context_var():
    """Verify request ID is properly set and retrieved in context."""
    assert get_request_id() is None
    set_request_id("test-req-123")
    assert get_request_id() == "test-req-123"
    set_request_id(None)
    assert get_request_id() is None


def test_structured_log_formatter_text():
    """Verify text formatting contains trace and agent details."""
    formatter = StructuredLogFormatter(json_output=False)
    record = logging.LogRecord(
        name="orca.test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Sample trace message",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-abc"
    record.agent = "ocean"

    output = formatter.format(record)
    assert "[req:req-abc]" in output
    assert "[ocean]" in output
    assert "Sample trace message" in output


def test_structured_log_formatter_json():
    """Verify JSON output formatting."""
    import json

    formatter = StructuredLogFormatter(json_output=True)
    record = logging.LogRecord(
        name="orca.test",
        level=logging.WARNING,
        pathname="test.py",
        lineno=20,
        msg="Warning event",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-xyz"
    record.agent = "weather"

    output = formatter.format(record)
    data = json.loads(output)
    assert data["level"] == "WARNING"
    assert data["request_id"] == "req-xyz"
    assert data["agent"] == "weather"
    assert data["message"] == "Warning event"


def test_get_logger_creation():
    """Verify get_logger returns a properly configured logger instance."""
    logger = get_logger("orca.test_unit", agent="commander")
    assert logger.name == "orca.test_unit"
    assert len(logger.handlers) >= 1
