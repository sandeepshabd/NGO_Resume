from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from time import perf_counter

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agents.orchestrator.main import handle_task as run_orchestrator
from skillbridge_common.jobs import JobSearchRequest, USAJobsClient
from skillbridge_common.logging import agent_logger, log_workflow_event
from skillbridge_common.planner import plan_career_workflow
from skillbridge_common.privacy import stable_hash
from skillbridge_common.schemas import TaskRequest, WorkflowEvent
from skillbridge_common.web import (
    ChatMessage,
    ChatRequest,
    Dashboard,
    InMemoryUserStore,
    ResumeRecord,
    UserContext,
)


app = FastAPI(title="SkillBridge Web API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
store = InMemoryUserStore()
jobs_client = USAJobsClient()
logger = agent_logger("skillbridge-web-api")


def _user_trace(user: UserContext) -> str:
    return f"user_{stable_hash(user.user_id) or 'anonymous'}"


async def current_user(authorization: str | None = Header(default=None)) -> UserContext:
    if os.getenv("FIREBASE_AUTH_ENABLED", "false").lower() == "true":
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        # Firebase Admin verification will be added when the GCP/Firebase project is selected.
        # For the POC, the dependency keeps the public API contract stable.
        token = authorization.removeprefix("Bearer ").strip()
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return UserContext(user_id=token[:32], auth_provider="firebase")

    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        return UserContext(user_id=token or "demo-user", email="demo@skillbridge.local")
    return UserContext(user_id="demo-user", email="demo@skillbridge.local")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "skillbridge-web-api"}


@app.post("/auth/demo-login", response_model=UserContext)
async def demo_login() -> UserContext:
    return UserContext(user_id="demo-user", email="demo@skillbridge.local")


@app.post("/api/resumes")
async def upload_resume(
    file: UploadFile = File(...),
    user: UserContext = Depends(current_user),
) -> dict[str, str]:
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload a text-based resume for the POC. PDF extraction will be added next.",
        )
    record = store.save_resume(
        ResumeRecord(user_id=user.user_id, filename=file.filename or "resume.txt", text=text)
    )
    log_workflow_event(
        logger,
        "resume_uploaded",
        workflow_id=record.id,
        trace_id=record.id,
        status="completed",
        user_id_hash=user.user_id,
        filename=record.filename,
        bytes_received=len(content),
        character_count=len(text),
    )
    return {"resume_id": record.id, "filename": record.filename}


@app.post("/api/chat", response_model=Dashboard)
async def chat(request: ChatRequest, user: UserContext = Depends(current_user)) -> Dashboard:
    start = perf_counter()
    resume_text = request.resume_text or store.latest_resume_text(user.user_id)
    if not resume_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload a resume or include resume_text before chatting.",
        )

    store.append_chat(user.user_id, ChatMessage(role="user", content=request.message))
    log_workflow_event(
        logger,
        "chat_workflow_started",
        workflow_id=_user_trace(user),
        trace_id=_user_trace(user),
        status="running",
        target_role=request.target_role,
        location=request.location,
        user_id_hash=user.user_id,
    )
    orchestration = await run_orchestrator(
        TaskRequest(
            user_id_hash=user.user_id,
            intent="career_readiness_workflow",
            skill_id="career_readiness_workflow",
            payload={
                "resume_text": resume_text,
                "target_role": request.target_role,
                "location": request.location,
            },
        )
    )
    keyword = request.target_role or "data analyst"
    jobs = await jobs_client.search(JobSearchRequest(keyword=keyword, location=request.location))
    log_workflow_event(
        logger,
        "job_search_completed",
        workflow_id=orchestration.task_id,
        trace_id=orchestration.trace_id,
        step_id="search_jobs",
        status="completed",
        target_role=request.target_role,
        location=request.location,
        result_count=len(jobs),
        source="USAJOBS" if jobs_client.configured else "demo",
    )
    result = orchestration.result
    answer = _chat_answer(result, jobs)
    store.append_chat(user.user_id, ChatMessage(role="assistant", content=answer))

    dashboard = Dashboard(
        profile=result.get("profile", {}),
        skill_graph=result.get("skill_graph", {}),
        learning_path=result.get("learning_path", {}),
        report=result.get("report", {}),
        jobs=jobs,
    )
    saved = store.save_dashboard(user.user_id, dashboard)
    log_workflow_event(
        logger,
        "chat_workflow_completed",
        workflow_id=orchestration.task_id,
        trace_id=orchestration.trace_id,
        status="completed",
        duration_ms=int((perf_counter() - start) * 1000),
        user_id_hash=user.user_id,
        job_count=len(jobs),
    )
    return saved


@app.get("/api/chat/events")
async def chat_events(
    message: str,
    target_role: str = "data analyst",
    location: str = "Texas",
    user_id: str = "demo-user",
) -> StreamingResponse:
    user = UserContext(user_id=user_id, email="demo@skillbridge.local")
    request = ChatRequest(message=message, target_role=target_role, location=location)
    return StreamingResponse(
        _chat_event_stream(request, user),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/dashboard", response_model=Dashboard)
async def dashboard(user: UserContext = Depends(current_user)) -> Dashboard:
    return store.get_dashboard(user.user_id)


@app.get("/api/jobs")
async def jobs(
    keyword: str = "data analyst",
    location: str = "Texas",
    user: UserContext = Depends(current_user),
) -> dict[str, object]:
    del user
    results = await jobs_client.search(JobSearchRequest(keyword=keyword, location=location))
    return {"jobs": results, "source": "USAJOBS" if jobs_client.configured else "demo"}


def _chat_answer(result: dict, jobs: list[dict]) -> str:
    report = result.get("report", {})
    gaps = report.get("priority_gaps", [])
    next_action = report.get("next_actions", ["Start with a focused portfolio artifact."])[0]
    job_count = len(jobs)
    gap_text = ", ".join(gaps[:3]) if gaps else "no major role gaps found"
    return (
        f"I reviewed your resume against the target role. Your top gaps are {gap_text}. "
        f"Start here: {next_action} I also found {job_count} job leads for the dashboard."
    )


async def _chat_event_stream(request: ChatRequest, user: UserContext) -> AsyncIterator[str]:
    stream_start = perf_counter()
    resume_text = request.resume_text or store.latest_resume_text(user.user_id)
    if not resume_text:
        yield _sse(
            WorkflowEvent(
                event="error",
                message="Upload a resume or include resume text before chatting.",
                status="failed",
            )
        )
        return

    plan = plan_career_workflow({"target_role": request.target_role})
    log_workflow_event(
        logger,
        "sse_workflow_planned",
        workflow_id=_user_trace(user),
        trace_id=_user_trace(user),
        status="planned",
        target_role=request.target_role,
        location=request.location,
        user_id_hash=user.user_id,
        step_count=len(plan.steps),
    )
    yield _sse(WorkflowEvent(event="plan", message=plan.objective, data=plan.model_dump()))

    store.append_chat(user.user_id, ChatMessage(role="user", content=request.message))
    for step in plan.steps:
        log_workflow_event(
            logger,
            "sse_step_emitted",
            workflow_id=_user_trace(user),
            trace_id=_user_trace(user),
            step_id=step.id,
            status="running",
            delegated_agent=step.agent,
        )
        yield _sse(
            WorkflowEvent(
                event="status",
                message=f"{step.label}: {step.reason}",
                step_id=step.id,
                agent=step.agent,
                status="running",
            )
        )

    orchestration = await run_orchestrator(
        TaskRequest(
            user_id_hash=user.user_id,
            intent="career_readiness_workflow",
            skill_id="career_readiness_workflow",
            payload={
                "resume_text": resume_text,
                "target_role": request.target_role,
                "location": request.location,
            },
        )
    )
    yield _sse(
        WorkflowEvent(
            event="status",
            message="Searching USAJOBS matches.",
            step_id="search_jobs",
            agent="job-market-agent",
            status="running",
        )
    )
    jobs = await jobs_client.search(
        JobSearchRequest(keyword=request.target_role, location=request.location)
    )
    log_workflow_event(
        logger,
        "sse_job_search_completed",
        workflow_id=orchestration.task_id,
        trace_id=orchestration.trace_id,
        step_id="search_jobs",
        status="completed",
        result_count=len(jobs),
        source="USAJOBS" if jobs_client.configured else "demo",
    )
    result = orchestration.result
    answer = _chat_answer(result, jobs)
    store.append_chat(user.user_id, ChatMessage(role="assistant", content=answer))
    dashboard = store.save_dashboard(
        user.user_id,
        Dashboard(
            profile=result.get("profile", {}),
            skill_graph=result.get("skill_graph", {}),
            learning_path=result.get("learning_path", {}),
            report=result.get("report", {}),
            jobs=jobs,
        ),
    )
    yield _sse(
        WorkflowEvent(
            event="complete",
            message="Agent workflow complete.",
            status="completed",
            data=dashboard.model_dump(mode="json"),
        )
    )
    log_workflow_event(
        logger,
        "sse_workflow_completed",
        workflow_id=orchestration.task_id,
        trace_id=orchestration.trace_id,
        status="completed",
        duration_ms=int((perf_counter() - stream_start) * 1000),
        job_count=len(jobs),
        user_id_hash=user.user_id,
    )


def _sse(event: WorkflowEvent) -> str:
    return f"event: {event.event}\ndata: {json.dumps(event.model_dump(mode='json'))}\n\n"
