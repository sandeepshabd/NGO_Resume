from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    user_id: str
    email: str | None = None
    auth_provider: str = "demo"


class ResumeRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"resume_{uuid4().hex}")
    user_id: str
    filename: str
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    message: str
    resume_text: str | None = None
    target_role: str = "data analyst"
    location: str = "Texas"


class Dashboard(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    skill_graph: dict[str, Any] = Field(default_factory=dict)
    learning_path: dict[str, Any] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)
    jobs: list[dict[str, Any]] = Field(default_factory=list)
    chat_history: list[ChatMessage] = Field(default_factory=list)


class InMemoryUserStore:
    def __init__(self) -> None:
        self.resumes: dict[str, list[ResumeRecord]] = {}
        self.dashboards: dict[str, Dashboard] = {}
        self.chats: dict[str, list[ChatMessage]] = {}

    def save_resume(self, record: ResumeRecord) -> ResumeRecord:
        self.resumes.setdefault(record.user_id, []).append(record)
        return record

    def latest_resume_text(self, user_id: str) -> str:
        records = self.resumes.get(user_id, [])
        return records[-1].text if records else ""

    def append_chat(self, user_id: str, message: ChatMessage) -> list[ChatMessage]:
        self.chats.setdefault(user_id, []).append(message)
        return self.chats[user_id]

    def save_dashboard(self, user_id: str, dashboard: Dashboard) -> Dashboard:
        dashboard.chat_history = self.chats.get(user_id, [])
        self.dashboards[user_id] = dashboard
        return dashboard

    def get_dashboard(self, user_id: str) -> Dashboard:
        dashboard = self.dashboards.get(user_id, Dashboard())
        dashboard.chat_history = self.chats.get(user_id, [])
        return dashboard

