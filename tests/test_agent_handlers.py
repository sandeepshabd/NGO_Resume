from __future__ import annotations

import asyncio

from agents.learning_path.main import handle_task as learning_path_handler
from agents.ops_autocorrect.main import handle_task as ops_handler
from agents.orchestrator.main import handle_task as orchestrator_handler
from agents.resume_parser.main import handle_task as resume_handler
from agents.skill_graph.main import handle_task as skill_graph_handler
from skillbridge_common.schemas import TaskRequest, TaskStatus


def run(coro):
    return asyncio.run(coro)


def test_resume_agent_returns_normalized_profile() -> None:
    response = run(
        resume_handler(
            TaskRequest(
                intent="parse resume",
                payload={"resume_text": "Jane Doe\n2 years Python SQL Excel dashboard work."},
            )
        )
    )

    assert response.status == TaskStatus.completed
    assert response.result["candidate_name"] == "Jane Doe"
    assert response.result["skills"] == ["excel", "python", "sql"]


def test_skill_graph_agent_returns_gap_analysis() -> None:
    response = run(
        skill_graph_handler(
            TaskRequest(
                intent="gap analysis",
                skill_id="gap_analysis",
                payload={"skills": ["Python", "SQL"], "target_role": "data analyst"},
            )
        )
    )

    assert response.status == TaskStatus.completed
    assert response.result["fit_score"] > 0
    assert "excel" in response.result["skill_gaps"]


def test_learning_path_agent_returns_steps() -> None:
    response = run(
        learning_path_handler(
            TaskRequest(
                intent="build path",
                payload={"skill_gaps": ["excel", "communication"], "weeks": 4},
            )
        )
    )

    assert response.status == TaskStatus.completed
    assert len(response.result["steps"]) == 2


def test_ops_agent_marks_rollback_as_approval_required() -> None:
    response = run(
        ops_handler(
            TaskRequest(
                intent="diagnose alert",
                payload={"service": "skillbridge", "severity": "critical", "error_rate": 0.3},
            )
        )
    )

    assert response.status == TaskStatus.needs_approval
    assert "rollback_previous_revision" in response.result["approval_required"]


def test_orchestrator_local_fallback_completes_without_registry(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_REGISTRY_JSON", "[]")
    response = run(
        orchestrator_handler(
            TaskRequest(
                intent="career workflow",
                payload={
                    "candidate_name": "Jane",
                    "resume_text": "Jane\nPython SQL project analyst work.",
                    "target_role": "data analyst",
                },
            )
        )
    )

    assert response.status == TaskStatus.completed
    assert response.result["execution_mode"] == "local_fallback"
    assert response.result["report"]["headline"] == "Jane career readiness plan for data analyst"

