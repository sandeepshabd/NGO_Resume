from __future__ import annotations

import os

from skillbridge_common.a2a import A2AClient, AgentRegistry
from skillbridge_common.app import create_agent_app
from skillbridge_common.schemas import AgentCard, AgentSkill, TaskRequest, TaskResponse, TaskStatus


CARD = AgentCard(
    name="skillbridge-orchestrator-agent",
    description="Routes SkillBridge user workflows to specialist A2A agents.",
    url=os.getenv("ORCHESTRATOR_URL", "http://skillbridge-orchestrator-agent"),
    skills=[
        AgentSkill(
            id="career_readiness_workflow",
            name="Career Readiness Workflow",
            description="Runs resume parsing, skill-gap analysis, matching, learning, and reporting.",
        )
    ],
)


async def _call_skill(
    registry: AgentRegistry,
    client: A2AClient,
    skill_id: str,
    parent: TaskRequest,
    payload: dict,
) -> TaskResponse | None:
    card = registry.find_by_skill(skill_id)
    if not card:
        return None
    return await client.send_task(
        card,
        TaskRequest(
            user_id_hash=parent.user_id_hash,
            intent=skill_id,
            skill_id=skill_id,
            payload=payload,
            trace_id=parent.trace_id,
        ),
    )


async def handle_task(request: TaskRequest) -> TaskResponse:
    registry = AgentRegistry.from_env()
    client = A2AClient()
    profile_payload = {
        "resume_text": request.payload.get("resume_text", ""),
        "candidate_name": request.payload.get("candidate_name"),
        "experience_summary": request.payload.get("experience_summary", ""),
    }

    resume = await _call_skill(registry, client, "parse_resume", request, profile_payload)
    profile = resume.result if resume else profile_payload

    target_role = request.payload.get("target_role", "data analyst")
    skill_graph = await _call_skill(
        registry,
        client,
        "gap_analysis",
        request,
        {"skills": profile.get("skills", []), "target_role": target_role},
    )
    gap_result = skill_graph.result if skill_graph else {"skill_gaps": [], "required_skills": []}

    matching = await _call_skill(
        registry,
        client,
        "score_match",
        request,
        {
            "skills": gap_result.get("normalized_skills", profile.get("skills", [])),
            "required_skills": gap_result.get("required_skills", []),
        },
    )

    learning = await _call_skill(
        registry,
        client,
        "build_learning_path",
        request,
        {"skill_gaps": gap_result.get("skill_gaps", []), "weeks": request.payload.get("weeks", 8)},
    )

    report = await _call_skill(
        registry,
        client,
        "write_career_report",
        request,
        {"profile": profile, "skill_gaps": gap_result.get("skill_gaps", [])},
    )

    return TaskResponse(
        task_id=request.task_id,
        agent=CARD.name,
        status=TaskStatus.completed,
        summary="Career readiness workflow completed.",
        result={
            "profile": profile,
            "skill_graph": gap_result,
            "match": matching.result if matching else None,
            "learning_path": learning.result if learning else None,
            "report": report.result if report else None,
            "agents_available": [card.name for card in registry.all_cards()],
        },
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)

