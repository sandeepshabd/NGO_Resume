from __future__ import annotations

from skillbridge_common.ops import diagnose_alert


def test_diagnose_alert_recommends_ticket_for_warning() -> None:
    diagnosis = diagnose_alert({"service": "skillbridge-report-writer-agent", "severity": "warning"})

    assert diagnosis["diagnosis"] == "general_health_check"
    assert diagnosis["auto_executable"] == ["open_incident_ticket"]
    assert diagnosis["approval_required"] == []


def test_diagnose_alert_requires_approval_for_high_error_rate() -> None:
    diagnosis = diagnose_alert(
        {
            "service": "skillbridge-orchestrator-agent",
            "severity": "critical",
            "error_rate": 0.35,
        }
    )

    assert diagnosis["diagnosis"] == "high_error_rate"
    assert "rollback_previous_revision" in diagnosis["approval_required"]

