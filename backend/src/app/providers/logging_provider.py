"""Logging provider abstraction.

This module exposes get_logger(name) which ensures structured logging is
configured the first time it is used. Other modules should import
get_logger and use it instead of calling logging.getLogger directly so the
application controls the log format in one place.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.logging_config import configure_logging


def _ensure_configured() -> None:
    root = logging.getLogger()
    # If no handlers are configured, set up structured logging now. If other
    # code (scripts) configured logging already (basicConfig), respect that.
    if not root.handlers:
        configure_logging()


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured to emit the project's structured format."""
    _ensure_configured()
    return logging.getLogger(name)
