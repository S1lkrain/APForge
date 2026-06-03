from __future__ import annotations

import logging
import re
from typing import Any

REDACTED = "[REDACTED]"

_SENSITIVE_FIELD_NAMES = frozenset(
    {
        "api_key",
        "openai_api_key",
        "apforge_core_api_key",
        "authorization",
        "x-llm-api-key",
        "x-api-key",
        "llm_api_key",
        "credentials",
        "byok_credentials",
        "bearer",
        "token",
        "secret",
    }
)

_REDACTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(Bearer\s+)[^\s'\",]+"), rf"\1{REDACTED}"),
    (re.compile(r"(?i)(Authorization\s*[:=]\s*)[^\s'\",]+"), rf"\1{REDACTED}"),
    (re.compile(r"(?i)(X-LLM-API-Key\s*[:=]\s*)[^\s'\",]+"), rf"\1{REDACTED}"),
    (re.compile(r"(?i)(X-API-Key\s*[:=]\s*)[^\s'\",]+"), rf"\1{REDACTED}"),
    (
        re.compile(
            r"(?i)((?:api_key|openai_api_key|apforge_core_api_key|llm_api_key)\s*[:=]\s*)"
            r"['\"]?[^'\",\s}]+['\"]?"
        ),
        rf"\1{REDACTED}",
    ),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"), REDACTED),
    (re.compile(r"\bsk-proj-[A-Za-z0-9_-]{8,}\b"), REDACTED),
]


def _normalize_field_name(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sensitive_field(name: str) -> bool:
    normalized = _normalize_field_name(name)
    if normalized in _SENSITIVE_FIELD_NAMES:
        return True
    return normalized.endswith("_api_key") or normalized.endswith("_key") and "api" in normalized


def redact_string(value: str) -> str:
    if not value:
        return value
    redacted = value
    for pattern, replacement in _REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, bytes):
        return REDACTED.encode()
    if isinstance(value, dict):
        return {
            key: REDACTED if _is_sensitive_field(str(key)) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        container_type = type(value)
        return container_type(redact_value(item) for item in value)
    if isinstance(value, BaseException):
        return redact_string(str(value))
    return value


def safe_exception_message(exc: BaseException) -> str:
    return redact_string(str(exc))


class SensitiveDataFilter(logging.Filter):
    """Strip API keys and credential material from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_string(record.msg)
        elif record.msg:
            record.msg = redact_string(str(record.msg))

        if record.args:
            if isinstance(record.args, dict):
                record.args = {key: redact_value(val) for key, val in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_value(arg) for arg in record.args)

        for key, value in list(record.__dict__.items()):
            if _is_sensitive_field(key):
                setattr(record, key, REDACTED)
            elif isinstance(value, str):
                setattr(record, key, redact_string(value))
            elif isinstance(value, dict):
                setattr(record, key, redact_value(value))

        if record.exc_info and record.exc_info[1] is not None:
            exc = record.exc_info[1]
            record.msg = f"{record.msg} ({safe_exception_message(exc)})"
        return True


def configure_logging() -> None:
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s request_id=%(request_id)s %(message)s",
        )
    if not any(isinstance(existing, SensitiveDataFilter) for existing in root.filters):
        sensitive_filter = SensitiveDataFilter()
        root.addFilter(sensitive_filter)
        for handler in root.handlers:
            if not any(isinstance(existing, SensitiveDataFilter) for existing in handler.filters):
                handler.addFilter(sensitive_filter)


class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = dict(kwargs.get("extra") or {})
        extra["request_id"] = self.extra.get("request_id", "-")
        kwargs["extra"] = redact_value(extra)
        return redact_string(msg) if isinstance(msg, str) else msg, kwargs
