from __future__ import annotations

from skillbridge_common.planner import plan_career_workflow


def test_plan_career_workflow_explains_agent_sequence() -> None:
    plan = plan_career_workflow({"target_role": "data analyst"})

    assert plan.objective == "Help the user understand readiness for data analyst and choose next actions."
    assert [step.skill_id for step in plan.steps] == [
        "parse_resume",
        "gap_analysis",
        "score_match",
        "build_learning_path",
        "write_career_report",
    ]
    assert plan.steps[0].agent == "resume-parser-agent"


def test_plan_marks_unavailable_agents_as_skipped() -> None:
    plan = plan_career_workflow(
        {"target_role": "data analyst"},
        available_agents=["resume-parser-agent"],
    )

    assert plan.steps[0].status == "planned"
    assert plan.steps[1].status == "skipped"
