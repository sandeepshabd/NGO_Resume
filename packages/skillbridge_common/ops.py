from __future__ import annotations

from typing import Any

from skillbridge_common.schemas import RemediationAction


def diagnose_alert(payload: dict[str, Any]) -> dict[str, Any]:
    severity = str(payload.get("severity", "warning")).lower()
    service = str(payload.get("service", "unknown-service"))
    error_rate = float(payload.get("error_rate", 0))
    latency_ms = float(payload.get("p95_latency_ms", 0))
    reason = "general_health_check"
    if error_rate >= 0.2:
        reason = "high_error_rate"
    elif latency_ms >= 8000:
        reason = "high_latency"
    elif "deployment" in str(payload.get("event", "")).lower():
        reason = "recent_deployment_risk"

    actions = [
        RemediationAction(
            id="open_incident_ticket",
            label=f"Open incident ticket for {service}",
            risk="low",
            requires_approval=False,
            command_type="ticket",
            parameters={"service": service, "severity": severity, "reason": reason},
        )
    ]

    if reason == "high_latency":
        actions.append(
            RemediationAction(
                id="reduce_concurrency_or_enable_fallback",
                label=f"Enable fallback path or reduce concurrency for {service}",
                risk="medium",
                requires_approval=True,
                command_type="feature_flag",
                parameters={"service": service, "flag": "use_lightweight_mode", "value": True},
            )
        )

    if severity in {"critical", "error"} or reason == "high_error_rate":
        actions.append(
            RemediationAction(
                id="rollback_previous_revision",
                label=f"Roll back {service} to previous healthy Cloud Run revision",
                risk="medium",
                requires_approval=True,
                command_type="rollback",
                parameters={"service": service},
            )
        )

    return {
        "service": service,
        "severity": severity,
        "diagnosis": reason,
        "recommended_actions": [action.model_dump() for action in actions],
        "auto_executable": [action.id for action in actions if not action.requires_approval],
        "approval_required": [action.id for action in actions if action.requires_approval],
    }

