from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    accepted = "accepted"
    working = "working"
    completed = "completed"
    failed = "failed"
    needs_approval = "needs_approval"


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class AgentCapabilities(BaseModel):
    streaming: bool = False
    task_status: bool = True
    human_approval: bool = False
    idempotent_tasks: bool = True


class AgentAuth(BaseModel):
    type: Literal["none", "iam", "oauth2"] = "iam"
    audience: str = "skillbridge-agents"


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    version: str = "0.1.0"
    owner: str = "SkillBridge AI"
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    skills: list[AgentSkill]
    auth: AgentAuth = Field(default_factory=AgentAuth)


class TaskRequest(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid4().hex}")
    user_id_hash: str | None = None
    intent: str
    skill_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskResponse(BaseModel):
    task_id: str
    agent: str
    status: TaskStatus
    summary: str
    result: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    trace_id: str
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentHealth(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    agent: str
    version: str = "0.1.0"


class RemediationAction(BaseModel):
    id: str
    label: str
    risk: Literal["low", "medium", "high"]
    requires_approval: bool
    command_type: Literal["rollback", "feature_flag", "queue_control", "ticket", "config_pr"]
    parameters: dict[str, Any] = Field(default_factory=dict)

