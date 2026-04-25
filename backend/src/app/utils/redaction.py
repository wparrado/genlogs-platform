"""PII redaction utilities for logging.

Provide redact_pii(obj) which recursively removes or masks sensitive
fields from dict/list/string payloads. Also provide redact_text_pii for
masking PII inside freeform strings.
"""
from __future__ import annotations

import re
from typing import Any

PII_KEYS = {
    "password",
    "passwd",
    "pass",
    "ssn",
    "social_security",
    "credit_card",
    "card_number",
    "token",
    "authorization",
    "auth",
    "email",
    "email_address",
    "name",
}


def _is_pii_key(key: str | None) -> bool:
    return bool(key) and key.lower() in PII_KEYS


def redact_text_pii(text: Any) -> Any:
    """Redact PII patterns inside freeform text.

    Non-string inputs are returned unchanged.
    """
    if not isinstance(text, str):
        return text

    # Emails
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]", text)
    # Credit-card like sequences (13-19 digits, possibly separated by spaces/dashes)
    text = re.sub(r"\b(?:\d[ \-]*?){13,19}\b", "[REDACTED_CC]", text)
    # SSN pattern
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", text)
    return text


def redact_pii(obj: Any) -> Any:
    """Recursively redact PII from dicts/lists/strings.

    Keys that match PII_KEYS will have their values replaced with "[REDACTED]".
    Strings will be scanned for common PII patterns.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if _is_pii_key(k):
                out[k] = "[REDACTED]"
            else:
                out[k] = redact_pii(v)
        return out
    if isinstance(obj, list):
        return [redact_pii(i) for i in obj]
    if isinstance(obj, str):
        return redact_text_pii(obj)
    return obj


# Header redaction (case-insensitive)
SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie"}


def redact_headers(headers: dict[str, str]) -> dict:
    """Return headers with sensitive values redacted.

    Preserves header names but replaces sensitive values with "[REDACTED]".
    Also applies text-level PII redaction to other header values.
    """
    out = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADERS:
            out[k] = "[REDACTED]"
        else:
            out[k] = redact_text_pii(v) if isinstance(v, str) else v
    return out
