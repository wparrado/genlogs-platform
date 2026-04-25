from __future__ import annotations

from contextvars import ContextVar
import uuid
from typing import Optional, Any

# Context var to hold request id per-request
_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    return uuid.uuid4().hex


def set_request_id(rid: str) -> Any:
    """Set the request id in the current context and return the token."""
    return _request_id_var.set(rid)


def get_request_id() -> Optional[str]:
    return _request_id_var.get()


def reset_request_id(token: Any) -> None:
    _request_id_var.reset(token)
