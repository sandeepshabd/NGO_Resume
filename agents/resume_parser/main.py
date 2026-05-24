from __future__ import annotations

from skillbridge_common.app import create_agent_app
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
    skills = sorted(
        {
            token.strip(".,;:()").lower()
            for token in resume_text.split()
            if token.strip(".,;:()").lower()
            in {"python", "sql", "excel", "salesforce", "java", "javascript", "cloud", "leadership"}
        }
    )
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Resume profile facts extracted.",
        result={
            "candidate_name": request.payload.get("candidate_name"),
            "skills": skills,
            "experience_summary": request.payload.get("experience_summary", ""),
            "source_quality": "text" if resume_text else "missing_resume_text",
        },
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)

