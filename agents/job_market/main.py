from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.schemas import AgentCard, AgentSkill, TaskRequest, TaskResponse, TaskStatus


CARD = AgentCard(
    name="job-market-agent",
    description="Finds target-role demand signals and representative job requirements.",
    url="http://job-market-agent",
    skills=[
        AgentSkill(
            id="job_market_scan",
            name="Job Market Scan",
            description="Returns role demand signals and common requirements for a location.",
        )
    ],
)


async def handle_task(request: TaskRequest) -> TaskResponse:
    target_role = request.payload.get("target_role", "data analyst")
    location = request.payload.get("location", "United States")
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Job market scan prepared.",
        result={
            "target_role": target_role,
            "location": location,
            "demand_level": "medium",
            "common_requirements": ["portfolio project", "resume keywords", "interview readiness"],
            "data_source": "placeholder_for_bigquery_or_partner_job_api",
        },
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)

