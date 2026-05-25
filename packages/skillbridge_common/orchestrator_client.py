from __future__ import annotations

import os

import httpx

from agents.orchestrator.main import handle_task as local_orchestrator
from skillbridge_common.schemas import TaskRequest, TaskResponse


class OrchestratorClient:
    def __init__(
        self,
        *,
        orchestrator_url: str | None = None,
        agent_token: str | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.orchestrator_url = (orchestrator_url or os.getenv("ORCHESTRATOR_URL", "")).rstrip("/")
        self.agent_token = agent_token or os.getenv("SKILLBRIDGE_AGENT_TOKEN")
        self.timeout_seconds = timeout_seconds

    @property
    def remote_enabled(self) -> bool:
        return bool(self.orchestrator_url)

    async def run_career_workflow(self, request: TaskRequest) -> TaskResponse:
        if not self.remote_enabled:
            return await local_orchestrator(request)

        headers = {}
        if self.agent_token:
            headers["x-skillbridge-agent-token"] = self.agent_token
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.orchestrator_url}/tasks",
                json=request.model_dump(mode="json"),
                headers=headers,
            )
            response.raise_for_status()
            return TaskResponse.model_validate(response.json())

