from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.career import build_learning_path
from skillbridge_common.llm import get_llm_client
from skillbridge_common.schemas import AgentCard, AgentSkill, TaskRequest, TaskResponse, TaskStatus


CARD = AgentCard(
    name="learning-path-agent",
    description="Builds practical learning plans from skill gaps and career goals.",
    url="http://learning-path-agent",
    skills=[
        AgentSkill(
            id="build_learning_path",
            name="Build Learning Path",
            description="Creates a prioritized roadmap for closing skill gaps.",
        )
    ],
)


async def handle_task(request: TaskRequest) -> TaskResponse:
    gaps = request.payload.get("skill_gaps", [])
    weeks = int(request.payload.get("weeks", 8))
    path = build_learning_path([str(gap) for gap in gaps], weeks)
    llm = get_llm_client()
    coaching_notes = await llm.complete_json(
        "Improve this learning path with concise coaching notes.",
        str(path),
    )
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Learning path generated.",
        result={**path, "coaching_notes": coaching_notes},
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)
