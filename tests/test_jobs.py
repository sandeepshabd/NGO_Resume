from __future__ import annotations

import pytest

from skillbridge_common.jobs import JobSearchRequest, USAJobsClient, demo_jobs, normalize_usajobs_item


def test_demo_jobs_return_when_credentials_are_missing() -> None:
    jobs = demo_jobs("data analyst", "Texas")

    assert jobs[0]["source"] == "demo"
    assert "Data Analyst" in jobs[0]["title"]


def test_normalize_usajobs_item_extracts_fields() -> None:
    item = {
        "MatchedObjectDescriptor": {
            "PositionID": "123",
            "PositionTitle": "Program Analyst",
            "OrganizationName": "Example Agency",
            "DepartmentName": "Example Department",
            "PositionURI": "https://www.usajobs.gov/job/123",
            "PositionLocation": [{"LocationName": "Dallas, Texas"}],
            "PositionRemuneration": [{"MinimumRange": "50000"}],
            "UserArea": {"Details": {"JobSummary": "Analyze programs."}},
        }
    }

    normalized = normalize_usajobs_item(item)

    assert normalized["id"] == "123"
    assert normalized["location"] == "Dallas, Texas"
    assert normalized["source"] == "USAJOBS"


@pytest.mark.anyio
async def test_usajobs_client_uses_demo_without_credentials(monkeypatch) -> None:
    monkeypatch.delenv("USAJOBS_EMAIL", raising=False)
    monkeypatch.delenv("USAJOBS_API_KEY", raising=False)
    client = USAJobsClient()

    jobs = await client.search(JobSearchRequest(keyword="cloud", location="Texas"))

    assert client.configured is False
    assert jobs[0]["source"] == "demo"

