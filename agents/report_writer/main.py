from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.schemas import AgentCard, AgentSkill, TaskRequest, TaskResponse, TaskStatus


CARD = AgentCard(
    name="report-writer-agent",
    description="Turns agent outputs into user-facing career plans and advisor reports.",
    url="http://report-writer-agent",
    skills=[
        AgentSkill(
            id="write_career_report",
            name="Write Career Report",
            description="Creates a concise career plan from profile, gap, and learning outputs.",
        )
    ],
)


async def handle_task(request: TaskRequest) -> TaskResponse:
    profile = request.payload.get("profile", {})
    gaps = request.payload.get("skill_gaps", [])
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Career report drafted.",
        result={
            "headline": "SkillBridge AI career readiness plan",
            "candidate": profile.get("candidate_name"),
            "priority_gaps": gaps[:5],
            "advisor_notes": "Review the plan with the candidate before sharing externally.",
        },
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)

