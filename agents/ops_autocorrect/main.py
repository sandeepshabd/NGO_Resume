from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.schemas import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    RemediationAction,
    TaskRequest,
    TaskResponse,
    TaskStatus,
)


CARD = AgentCard(
    name="ops-autocorrect-agent",
    description="Diagnoses observability alerts and proposes controlled remediation actions.",
    url="http://ops-autocorrect-agent",
    capabilities=AgentCapabilities(human_approval=True),
    skills=[
        AgentSkill(
            id="diagnose_alert",
            name="Diagnose Alert",
            description="Classifies an incident and returns safe remediation options.",
        )
    ],
)


async def handle_task(request: TaskRequest) -> TaskResponse:
    severity = request.payload.get("severity", "warning")
    service = request.payload.get("service", "unknown-service")
    actions = [
        RemediationAction(
            id="open_incident_ticket",
            label=f"Open incident ticket for {service}",
            risk="low",
            requires_approval=False,
            command_type="ticket",
            parameters={"service": service, "severity": severity},
        )
    ]
    if severity in {"critical", "error"}:
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
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.needs_approval if any(a.requires_approval for a in actions) else TaskStatus.completed,
        summary="Alert diagnosis completed.",
        result={"service": service, "severity": severity, "recommended_actions": [a.model_dump() for a in actions]},
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)

