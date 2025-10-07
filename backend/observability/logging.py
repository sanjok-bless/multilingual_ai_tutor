"""Structured logging configuration with JSON output."""

import logging
import sys

import structlog
from structlog.types import EventDict, WrappedLogger


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get configured logger."""
    return structlog.get_logger(name)


def add_severity(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add log severity to event_dict using 'severity' field (RFC 5424/GCP standard)."""
    if method_name == "warn":
        method_name = "warning"
    event_dict["severity"] = method_name
    return event_dict


def reorder_fields(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Move ts, severity, event to front for consistent JSON output."""
    return {
        **{k: event_dict.pop(k) for k in ("ts", "severity", "event") if k in event_dict},
        **event_dict,
    }


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured JSON logging."""
    # Configure structlog processors
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", key="ts"),
            add_severity,
            structlog.contextvars.merge_contextvars,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            reorder_fields,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure ProcessorFormatter for standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=[
            structlog.processors.TimeStamper(fmt="iso", key="ts"),
            add_severity,
            structlog.processors.format_exc_info,
            reorder_fields,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Configure uvicorn startup/error/access loggers to use structlog
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True

    # Disable duplicate access logs from uvicorn (we have custom middleware)
    logging.getLogger("uvicorn.access").disabled = True

    # Suppress httpx and httpcore INFO logs (OpenAI API calls)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
