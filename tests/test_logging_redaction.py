from __future__ import annotations

import logging

from ap_skill_generator.logging_utils import (
    REDACTED,
    SensitiveDataFilter,
    redact_string,
    redact_value,
    safe_exception_message,
)


def test_redact_string_bearer_and_sk_keys():
    raw = "Authorization: Bearer sk-test1234567890 api_key=sk-abc1234567890"
    redacted = redact_string(raw)
    assert "sk-test" not in redacted
    assert "sk-abc" not in redacted
    assert REDACTED in redacted


def test_redact_string_header_aliases():
    raw = "X-LLM-API-Key: secret-value X-API-Key: access-secret"
    redacted = redact_string(raw)
    assert "secret-value" not in redacted
    assert "access-secret" not in redacted


def test_redact_value_sensitive_dict_keys():
    payload = {
        "api_key": "sk-live",
        "openai_api_key": "sk-openai",
        "run_id": "abc",
        "nested": {"Authorization": "Bearer sk-nested"},
    }
    redacted = redact_value(payload)
    assert redacted["api_key"] == REDACTED
    assert redacted["openai_api_key"] == REDACTED
    assert redacted["run_id"] == "abc"
    assert redacted["nested"]["Authorization"] == REDACTED


def test_sensitive_data_filter_on_log_record():
    logger = logging.getLogger("test.redaction")
    records: list[logging.LogRecord] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = CaptureHandler()
    handler.addFilter(SensitiveDataFilter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info(
        "BYOK connect api_key=sk-abcdef0123456789",
        extra={"openai_api_key": "sk-extra", "request_id": "req-1"},
    )
    assert records
    record = records[0]
    assert "sk-abcdef" not in record.msg
    assert record.openai_api_key == REDACTED
    assert record.request_id == "req-1"


def test_safe_exception_message():
    assert REDACTED in safe_exception_message(RuntimeError("Bearer sk-badkey1234567890"))
