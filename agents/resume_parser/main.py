from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.career import infer_target_roles, parse_resume_text
from skillbridge_common.llm import get_llm_client
from skillbridge_common.schemas import AgentCard, AgentSkill, TaskRequest, TaskResponse, TaskStatus


CARD = AgentCard(
    name="resume-parser-agent",
    description="Extracts structured experience, education, projects, and skills from resumes.",
    url="http://resume-parser-agent",
    skills=[
        AgentSkill(
            id="parse_resume",
            name="Parse Resume",
            description="Parses resume text or document metadata into normalized profile facts.",
        )
    ],
)


async def handle_task(request: TaskRequest) -> TaskResponse:
    resume_text = request.payload.get("resume_text", "")
    profile = parse_resume_text(
        resume_text,
        candidate_name=request.payload.get("candidate_name"),
        experience_summary=request.payload.get("experience_summary"),
    )
    llm = get_llm_client()
    enrichment = await llm.complete_json(
        "Extract resume insights as JSON. Do not invent facts.",
        resume_text[:4000],
    )
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Resume profile facts extracted and normalized.",
        result={
            **profile.as_dict(),
            "suggested_target_roles": infer_target_roles(resume_text),
            "llm_enrichment": enrichment,
        },
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)
