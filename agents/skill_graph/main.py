from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.schemas import AgentCard, AgentSkill, TaskRequest, TaskResponse, TaskStatus


SKILL_ALIASES = {
    "js": "javascript",
    "gcp": "google cloud",
    "google cloud platform": "google cloud",
    "ms excel": "excel",
}

ROLE_BASELINES = {
    "data analyst": {"sql", "excel", "python", "data visualization", "communication"},
    "cloud support associate": {"google cloud", "linux", "networking", "python", "customer support"},
    "project coordinator": {"communication", "excel", "planning", "stakeholder management"},
}

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
    normalized = sorted({SKILL_ALIASES.get(str(skill).lower(), str(skill).lower()) for skill in raw_skills})
    target_role = str(request.payload.get("target_role", "data analyst")).lower()
    required = ROLE_BASELINES.get(target_role, set())
    gaps = sorted(required.difference(normalized))
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Skill graph analysis completed.",
        result={
            "normalized_skills": normalized,
            "target_role": target_role,
            "required_skills": sorted(required),
            "skill_gaps": gaps,
            "fit_score": round(1 - (len(gaps) / max(len(required), 1)), 2),
        },
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)

