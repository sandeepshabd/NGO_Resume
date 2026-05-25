from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.career import analyze_skill_gap, normalize_skills
from skillbridge_common.schemas import AgentCard, AgentSkill, TaskRequest, TaskResponse, TaskStatus


CARD = AgentCard(
    name="skill-graph-agent",
    description="Normalizes skills and maps skill gaps against target roles.",
    url="http://skill-graph-agent",
    skills=[
        AgentSkill(
            id="normalize_skills",
            name="Normalize Skills",
            description="Converts raw skills into canonical skill names.",
        ),
        AgentSkill(
            id="gap_analysis",
            name="Skill Gap Analysis",
            description="Compares candidate skills with a target role baseline.",
        ),
    ],
)


async def handle_task(request: TaskRequest) -> TaskResponse:
    raw_skills = request.payload.get("skills", [])
    normalized = normalize_skills([str(skill) for skill in raw_skills])
    target_role = str(request.payload.get("target_role", "data analyst")).lower()
    if request.skill_id == "normalize_skills":
        result = {"normalized_skills": normalized}
    else:
        result = analyze_skill_gap(normalized, target_role)
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Skill graph analysis completed.",
        result=result,
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)
