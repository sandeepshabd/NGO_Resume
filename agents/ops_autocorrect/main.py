from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.ops import diagnose_alert
from skillbridge_common.schemas import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
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
    diagnosis = diagnose_alert(request.payload)
    needs_approval = bool(diagnosis["approval_required"])
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.needs_approval if needs_approval else TaskStatus.completed,
        summary="Alert diagnosis completed.",
        result=diagnosis,
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)
