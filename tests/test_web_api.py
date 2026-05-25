from __future__ import annotations

from fastapi.testclient import TestClient

from agents.web_api.main import app


def test_demo_login() -> None:
    client = TestClient(app)

    response = client.post("/auth/demo-login")

    assert response.status_code == 200
    assert response.json()["user_id"] == "demo-user"


def test_resume_upload_and_chat_workflow(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_REGISTRY_JSON", "[]")
    client = TestClient(app)

    upload = client.post(
        "/api/resumes",
        files={"file": ("resume.txt", b"Jane Doe\nPython SQL Excel project work.", "text/plain")},
    )
    assert upload.status_code == 200

    chat = client.post(
        "/api/chat",
        json={
            "message": "What jobs fit me?",
            "target_role": "data analyst",
            "location": "Texas",
        },
    )

    assert chat.status_code == 200
    body = chat.json()
    assert body["profile"]["candidate_name"] == "Jane Doe"
    assert body["jobs"]
    assert body["chat_history"][-1]["role"] == "assistant"


def test_jobs_endpoint_returns_demo_source(monkeypatch) -> None:
    monkeypatch.delenv("USAJOBS_EMAIL", raising=False)
    monkeypatch.delenv("USAJOBS_API_KEY", raising=False)
    client = TestClient(app)

    response = client.get("/api/jobs?keyword=analyst&location=Texas")

    assert response.status_code == 200
    assert response.json()["source"] == "demo"

