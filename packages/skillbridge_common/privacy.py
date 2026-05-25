from __future__ import annotations

import hashlib
import re
from typing import Any


SENSITIVE_KEYS = {
    "authorization",
    "token",
    "api_key",
    "apikey",
    "password",
    "secret",
    "resume_text",
    "text",
    "phone",
    "email",
    "candidate_name",
    "message",
    "content",
    "filename",
}

EMAIL_RE = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


def stable_hash(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return redact_dict(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return PHONE_RE.sub("[REDACTED_PHONE]", EMAIL_RE.sub("[REDACTED_EMAIL]", value))
    return value


def redact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        normalized_key = key.lower()
        if any(sensitive in normalized_key for sensitive in SENSITIVE_KEYS):
            redacted[key] = "[REDACTED]"
        elif normalized_key in {"user_id", "user_id_hash"}:
            redacted[key] = stable_hash(str(value))
        else:
            redacted[key] = redact_value(value)
    return redacted
