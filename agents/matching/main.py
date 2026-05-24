from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.schemas import AgentCard, AgentSkill, TaskRequest, TaskResponse, TaskStatus


CARD = AgentCard(
    name="matching-agent",
    description="Scores candidate profiles against roles, programs, and opportunities.",
    url="http://matching-agent",
    skills=[
        AgentSkill(
            id="score_match",
            name="Score Match",
            description="Scores the user profile against a role or opportunity requirement set.",
        )
    ],
)


async def handle_task(request: TaskRequest) -> TaskResponse:
    skills = set(request.payload.get("skills", []))
    required = set(request.payload.get("required_skills", []))
    overlap = sorted(skills.intersection(required))
    missing = sorted(required.difference(skills))
    score = round(len(overlap) / max(len(required), 1), 2)
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Candidate match score calculated.",
        result={"score": score, "matched_skills": overlap, "missing_skills": missing},
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)

