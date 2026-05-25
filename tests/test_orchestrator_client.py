from __future__ import annotations

import pytest

from skillbridge_common.orchestrator_client import OrchestratorClient
from skillbridge_common.schemas import TaskRequest, TaskStatus


@pytest.mark.anyio
async def test_orchestrator_client_uses_local_fallback_when_url_is_empty(monkeypatch) -> None:
    monkeypatch.delenv("ORCHESTRATOR_URL", raising=False)
    monkeypatch.setenv("AGENT_REGISTRY_JSON", "[]")
    client = OrchestratorClient(orchestrator_url="")

    response = await client.run_career_workflow(
        TaskRequest(
            intent="career_readiness_workflow",
            payload={
                "resume_text": "Jane Doe\nPython SQL Excel project work.",
                "target_role": "data analyst",
            },
        )
    )

    assert client.remote_enabled is False
    assert response.status == TaskStatus.completed
    assert response.result["execution_mode"] == "local_fallback"

