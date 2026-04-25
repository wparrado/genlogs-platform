"""Structured logging helpers used by the application.

Provides a JSONFormatter and configure_logging() helper to emit compact JSON
logs that include a request_id when available.
"""

import logging
import json
import os
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Simple JSON log formatter.

    Emits a compact JSON object with timestamp, level, logger, message and
    optional exception text and any extra fields set on the LogRecord.
    """

    def format(self, record: logging.LogRecord) -> str:
        record_dict = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat().replace('+00:00', 'Z'),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach current request id from context if not provided on the record
        try:
            from app.utils.request_id import get_request_id

            if "request_id" not in record.__dict__:
                rid = get_request_id()
                if rid:
                    record_dict["request_id"] = rid
        except ImportError:
            # If request id module isn't available for some reason, skip it
            pass

        # Include exception text if present
        if record.exc_info:
            record_dict["exc"] = self.formatException(record.exc_info)

        # Include any extra keys attached to the record
        ignored = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
        }
        for k, v in record.__dict__.items():
            if k not in ignored:
                # only include JSON-serializable values
                try:
                    json.dumps(v)
                    record_dict[k] = v
                except (TypeError, ValueError):
                    record_dict[k] = str(v)

        return json.dumps(record_dict, ensure_ascii=False)


def configure_logging(level: str | None = None) -> None:
    """Configure root logger to emit structured JSON to stdout.

    Should be called once at application startup (before other modules log).
    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    try:
        lvl = getattr(logging, level.upper())
    except AttributeError:
        lvl = logging.INFO

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    # remove existing handlers to avoid duplicate logs
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(lvl)
    root.addHandler(handler)

    # Let third-party loggers propagate to root so they use JSON output
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "gunicorn", "gunicorn.error"):
        log = logging.getLogger(name)
        log.handlers = []
        log.propagate = True
