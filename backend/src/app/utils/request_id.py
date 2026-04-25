"""Request ID context helpers.

This module provides a small ContextVar-based helper to generate and store a
request identifier that can be attached to logs or traced throughout a request
lifecycle.
"""
from __future__ import annotations

from contextvars import ContextVar
import uuid
from typing import Optional, Any

# Context var to hold request id per-request
_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    """Generate a new opaque request identifier string.

    The implementation uses a UUID4 hex string for compactness.
    """
    return uuid.uuid4().hex


def set_request_id(rid: str) -> Any:
    """Set the request id in the current context and return the token.

    The returned token can be passed to reset_request_id() to restore the
    previous context value.
    """
    return _request_id_var.set(rid)


def get_request_id() -> Optional[str]:
    """Return the currently-set request id for this context, or None."""
    return _request_id_var.get()


def reset_request_id(token: Any) -> None:
    """Reset the request id ContextVar using the provided token."""
    _request_id_var.reset(token)
