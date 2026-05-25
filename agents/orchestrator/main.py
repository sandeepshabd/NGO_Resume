from __future__ import annotations

import os
from time import perf_counter

from skillbridge_common.a2a import A2AClient, AgentRegistry
from skillbridge_common.app import create_agent_app
from skillbridge_common.career import (
    analyze_skill_gap,
    build_learning_path,
    parse_resume_text,
    write_career_report,
)
from skillbridge_common.logging import agent_logger, log_workflow_event
from skillbridge_common.planner import plan_career_workflow
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
logger = agent_logger(CARD.name)


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
    start = perf_counter()
    log_workflow_event(
        logger,
        "agent_step_started",
        workflow_id=parent.task_id,
        trace_id=parent.trace_id,
        step_id=skill_id,
        status="running",
        delegated_agent=card.name,
        payload_keys=sorted(payload.keys()),
    )
    try:
        response = await client.send_task(
            card,
            TaskRequest(
                user_id_hash=parent.user_id_hash,
                intent=skill_id,
                skill_id=skill_id,
                payload=payload,
                trace_id=parent.trace_id,
            ),
        )
        log_workflow_event(
            logger,
            "agent_step_completed",
            workflow_id=parent.task_id,
            trace_id=parent.trace_id,
            step_id=skill_id,
            status=response.status,
            duration_ms=int((perf_counter() - start) * 1000),
            delegated_agent=card.name,
        )
        return response
    except Exception as exc:
        log_workflow_event(
            logger,
            "agent_step_failed",
            workflow_id=parent.task_id,
            trace_id=parent.trace_id,
            step_id=skill_id,
            status="failed",
            duration_ms=int((perf_counter() - start) * 1000),
            delegated_agent=card.name,
            error_type=type(exc).__name__,
        )
        return None


async def handle_task(request: TaskRequest) -> TaskResponse:
    workflow_start = perf_counter()
    registry = AgentRegistry.from_env()
    client = A2AClient()
    plan = plan_career_workflow(
        request.payload,
        available_agents=[card.name for card in registry.all_cards()],
    )
    log_workflow_event(
        logger,
        "workflow_planned",
        workflow_id=request.task_id,
        trace_id=request.trace_id,
        status="planned",
        step_count=len(plan.steps),
        execution_mode="a2a" if registry.all_cards() else "local_fallback",
        target_role=request.payload.get("target_role", "data analyst"),
        user_id_hash=request.user_id_hash,
    )
    profile_payload = {
        "resume_text": request.payload.get("resume_text", ""),
        "candidate_name": request.payload.get("candidate_name"),
        "experience_summary": request.payload.get("experience_summary", ""),
    }

    resume = await _call_skill(registry, client, "parse_resume", request, profile_payload)
    log_workflow_event(
        logger,
        "local_or_remote_step_completed",
        workflow_id=request.task_id,
        trace_id=request.trace_id,
        step_id="parse_resume",
        status="completed",
        source="a2a" if resume else "local_fallback",
    )
    profile = (
        resume.result
        if resume
        else parse_resume_text(
            profile_payload["resume_text"],
            candidate_name=profile_payload["candidate_name"],
            experience_summary=profile_payload["experience_summary"],
        ).as_dict()
    )

    target_role = request.payload.get("target_role", "data analyst")
    skill_graph = await _call_skill(
        registry,
        client,
        "gap_analysis",
        request,
        {"skills": profile.get("skills", []), "target_role": target_role},
    )
    gap_result = skill_graph.result if skill_graph else analyze_skill_gap(profile.get("skills", []), target_role)
    log_workflow_event(
        logger,
        "local_or_remote_step_completed",
        workflow_id=request.task_id,
        trace_id=request.trace_id,
        step_id="gap_analysis",
        status="completed",
        source="a2a" if skill_graph else "local_fallback",
        skill_count=len(profile.get("skills", [])),
        gap_count=len(gap_result.get("skill_gaps", [])),
    )

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
    learning_result = learning.result if learning else build_learning_path(
        gap_result.get("skill_gaps", []),
        int(request.payload.get("weeks", 8)),
    )
    log_workflow_event(
        logger,
        "local_or_remote_step_completed",
        workflow_id=request.task_id,
        trace_id=request.trace_id,
        step_id="build_learning_path",
        status="completed",
        source="a2a" if learning else "local_fallback",
        step_count=len(learning_result.get("steps", [])),
    )

    report = await _call_skill(
        registry,
        client,
        "write_career_report",
        request,
        {"profile": profile, "gap_analysis": gap_result, "learning_path": learning_result},
    )
    report_result = report.result if report else write_career_report(profile, gap_result, learning_result)
    log_workflow_event(
        logger,
        "workflow_completed",
        workflow_id=request.task_id,
        trace_id=request.trace_id,
        status="completed",
        duration_ms=int((perf_counter() - workflow_start) * 1000),
        source="a2a" if report else "local_fallback",
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
            "learning_path": learning_result,
            "report": report_result,
            "plan": plan.model_dump(),
            "agents_available": [card.name for card in registry.all_cards()],
            "execution_mode": "a2a" if registry.all_cards() else "local_fallback",
        },
        trace_id=request.trace_id,
    )


app = create_agent_app(CARD, handle_task)
