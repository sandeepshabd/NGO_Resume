from __future__ import annotations

from typing import Any

from skillbridge_common.schemas import WorkflowPlan, WorkflowStep


def plan_career_workflow(payload: dict[str, Any], available_agents: list[str] | None = None) -> WorkflowPlan:
    target_role = str(payload.get("target_role") or "target role")
    available = set(available_agents or [])
    steps = [
        WorkflowStep(
            id="parse_resume",
            agent="resume-parser-agent",
            skill_id="parse_resume",
            label="Read resume",
            reason="Extract profile facts, skills, education, projects, and contact signals.",
            status=_initial_status("resume-parser-agent", available),
        ),
        WorkflowStep(
            id="analyze_skill_gap",
            agent="skill-graph-agent",
            skill_id="gap_analysis",
            label="Compare skills",
            reason=f"Compare the candidate profile against the {target_role} baseline.",
            status=_initial_status("skill-graph-agent", available),
        ),
        WorkflowStep(
            id="score_match",
            agent="matching-agent",
            skill_id="score_match",
            label="Score readiness",
            reason="Calculate match score from strengths and missing role requirements.",
            status=_initial_status("matching-agent", available),
        ),
        WorkflowStep(
            id="build_learning_path",
            agent="learning-path-agent",
            skill_id="build_learning_path",
            label="Plan learning",
            reason="Turn skill gaps into a short practical roadmap.",
            status=_initial_status("learning-path-agent", available),
        ),
        WorkflowStep(
            id="write_report",
            agent="report-writer-agent",
            skill_id="write_career_report",
            label="Write advisor report",
            reason="Summarize readiness, next actions, and advisor notes for the user.",
            status=_initial_status("report-writer-agent", available),
        ),
    ]
    return WorkflowPlan(
        objective=f"Help the user understand readiness for {target_role} and choose next actions.",
        steps=steps,
    )


def _initial_status(agent: str, available: set[str]) -> str:
    if not available:
        return "planned"
    return "planned" if agent in available else "skipped"

