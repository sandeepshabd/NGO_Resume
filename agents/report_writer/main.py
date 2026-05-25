from __future__ import annotations

from skillbridge_common.app import create_agent_app
from skillbridge_common.career import write_career_report
from skillbridge_common.llm import get_llm_client
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
    gap_analysis = request.payload.get("gap_analysis", {"skill_gaps": request.payload.get("skill_gaps", [])})
    learning_path = request.payload.get("learning_path")
    report = write_career_report(profile, gap_analysis, learning_path)
    llm = get_llm_client()
    narrative = await llm.complete_json(
        "Convert this structured career report into a warm concise advisor narrative.",
        str(report),
    )
    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Career report drafted.",
        result={**report, "narrative": narrative},
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)
