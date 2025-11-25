"""
Logging configuration for Agent Council system.

Implements structured logging with PII/secret redaction for compliance.
All logs are JSON-formatted for easy parsing and analysis.
"""

import logging
import re
import sys
from typing import Any

import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import add_log_level, filter_by_level

from app.utils.settings import get_settings


# Patterns for sensitive data redaction
SENSITIVE_PATTERNS = [
    (re.compile(r'(api[_-]?key["\s:=]+)([^\s,}"]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(secret["\s:=]+)([^\s,}"]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(password["\s:=]+)([^\s,}"]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(token["\s:=]+)([^\s,}"]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(bearer\s+)([^\s,}"]+)', re.IGNORECASE), r'\1***REDACTED***'),
    # Email patterns (potential PII)
    (re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE), r'***EMAIL_REDACTED***'),
    # Customer IDs (Salesforce patterns)
    (re.compile(r'(customer[_-]?id["\s:=]+)([^\s,}"]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(account[_-]?id["\s:=]+)([^\s,}"]+)', re.IGNORECASE), r'\1***REDACTED***'),
]


def redact_sensitive_data(message: str) -> str:
    """
    Redact sensitive information from log messages.

    Args:
        message: The log message to redact

    Returns:
        Redacted message with sensitive data replaced
    """
    redacted = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def add_redaction(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """
    Processor to redact sensitive data from log events.

    Args:
        logger: The logger instance
        method_name: The logging method name
        event_dict: The event dictionary

    Returns:
        Redacted event dictionary
    """
    # Redact the main event message
    if "event" in event_dict:
        event_dict["event"] = redact_sensitive_data(str(event_dict["event"]))

    # Redact any string values in the context
    for key, value in event_dict.items():
        if isinstance(value, str):
            event_dict[key] = redact_sensitive_data(value)

    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up structlog with JSON output, log level filtering, and PII redaction.
    """
    settings = get_settings()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level.upper(),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            filter_by_level,
            add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.contextvars.merge_contextvars,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_redaction,  # Custom redaction processor
            JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)

