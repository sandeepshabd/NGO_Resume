from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.schemas import AgentCard, AgentSkill, TaskRequest, TaskResponse, TaskStatus


CARD = AgentCard(
    name="interview-coach-agent",
    description="Generates interview practice prompts and structured feedback rubrics.",
    url="http://interview-coach-agent",
    skills=[
        AgentSkill(
            id="mock_interview",
            name="Mock Interview",
            description="Creates interview questions and a scoring rubric for a target role.",
        )
    ],
)


async def handle_task(request: TaskRequest) -> TaskResponse:
    target_role = request.payload.get("target_role", "target role")
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Interview practice generated.",
        result={
            "questions": [
                f"Tell me about a project that prepared you for a {target_role} role.",
                "Describe a time you learned a new technical skill quickly.",
                "How would you explain a complex problem to a non-technical stakeholder?",
            ],
            "rubric": ["clarity", "role relevance", "specific evidence", "reflection"],
        },
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)

