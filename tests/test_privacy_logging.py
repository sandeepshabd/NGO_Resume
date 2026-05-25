from __future__ import annotations

import logging

from skillbridge_common.logging import agent_logger, log_workflow_event
from skillbridge_common.privacy import redact_dict, stable_hash


def test_redact_dict_masks_sensitive_fields() -> None:
    payload = redact_dict(
        {
            "email": "jane@example.com",
            "phone": "214-555-1212",
            "resume_text": "Jane Doe jane@example.com 214-555-1212",
            "nested": {"message": "hello", "notes": "call 214-555-1212"},
            "user_id_hash": "real-user-id",
        }
    )

    assert payload["email"] == "[REDACTED]"
    assert payload["phone"] == "[REDACTED]"
    assert payload["resume_text"] == "[REDACTED]"
    assert payload["nested"]["message"] == "[REDACTED]"
    assert payload["nested"]["notes"] == "call [REDACTED_PHONE]"
    assert payload["user_id_hash"] == stable_hash("real-user-id")


def test_log_workflow_event_does_not_emit_raw_pii(caplog) -> None:
    logger = agent_logger("test-agent")

    with caplog.at_level(logging.INFO):
        log_workflow_event(
            logger,
            "workflow_planned",
            workflow_id="workflow-1",
            trace_id="trace-1",
            status="planned",
            email="jane@example.com",
            resume_text="Jane Doe jane@example.com",
            user_id_hash="real-user-id",
        )

    record = caplog.records[0]
    assert record.email == "[REDACTED]"
    assert record.resume_text == "[REDACTED]"
    assert record.user_id_hash == stable_hash("real-user-id")
    assert "jane@example.com" not in caplog.text
