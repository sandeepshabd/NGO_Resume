from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, FastAPI

from skillbridge_common.logging import agent_logger, configure_logging, log_task_event
from skillbridge_common.schemas import AgentCard, AgentHealth, TaskRequest, TaskResponse
from skillbridge_common.security import require_agent_token

TaskHandler = Callable[[TaskRequest], Awaitable[TaskResponse]]


def create_agent_app(card: AgentCard, handler: TaskHandler) -> FastAPI:
    configure_logging()
    logger = agent_logger(card.name)
    app = FastAPI(title=card.name, version=card.version)

    @app.get("/healthz", response_model=AgentHealth)
    async def healthz() -> AgentHealth:
        return AgentHealth(agent=card.name, version=card.version)

    @app.get("/.well-known/agent-card.json", response_model=AgentCard)
    async def agent_card() -> AgentCard:
        return card

    @app.post("/tasks", response_model=TaskResponse, dependencies=[Depends(require_agent_token)])
    async def run_task(request: TaskRequest) -> TaskResponse:
        log_task_event(logger, "task_received", task_id=request.task_id, trace_id=request.trace_id)
        response = await handler(request)
        log_task_event(
            logger,
            "task_completed",
            task_id=request.task_id,
            trace_id=request.trace_id,
            status=response.status,
        )
        return response

    return app

