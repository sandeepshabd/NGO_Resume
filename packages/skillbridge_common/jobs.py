from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class JobSearchRequest:
    keyword: str
    location: str = "Texas"
    results_per_page: int = 10
    page: int = 1


class USAJobsClient:
    base_url = "https://data.usajobs.gov/api/Search"

    def __init__(
        self,
        *,
        email: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.email = email or os.getenv("USAJOBS_EMAIL")
        self.api_key = api_key or os.getenv("USAJOBS_API_KEY")
        self.timeout_seconds = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self.email and self.api_key)

    async def search(self, request: JobSearchRequest) -> list[dict[str, Any]]:
        if not self.configured:
            return demo_jobs(request.keyword, request.location)

        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": self.email or "",
            "Authorization-Key": self.api_key or "",
        }
        params = {
            "Keyword": request.keyword,
            "LocationName": request.location,
            "ResultsPerPage": min(max(request.results_per_page, 1), 25),
            "Page": max(request.page, 1),
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()
        items = payload.get("SearchResult", {}).get("SearchResultItems", [])
        return [normalize_usajobs_item(item) for item in items]


def normalize_usajobs_item(item: dict[str, Any]) -> dict[str, Any]:
    descriptor = item.get("MatchedObjectDescriptor", {})
    locations = descriptor.get("PositionLocation", [])
    remuneration = descriptor.get("PositionRemuneration", [])
    return {
        "id": descriptor.get("PositionID"),
        "title": descriptor.get("PositionTitle"),
        "organization": descriptor.get("OrganizationName"),
        "department": descriptor.get("DepartmentName"),
        "location": ", ".join(
            location.get("LocationName", "") for location in locations if location.get("LocationName")
        ),
        "apply_url": descriptor.get("PositionURI"),
        "summary": descriptor.get("UserArea", {}).get("Details", {}).get("JobSummary"),
        "salary": remuneration[0] if remuneration else {},
        "source": "USAJOBS",
    }


def demo_jobs(keyword: str, location: str) -> list[dict[str, Any]]:
    clean_keyword = keyword or "data analyst"
    return [
        {
            "id": "demo-usajobs-1",
            "title": f"{clean_keyword.title()} Trainee",
            "organization": "Demo Federal Agency",
            "department": "SkillBridge Demo",
            "location": location,
            "apply_url": "https://www.usajobs.gov/Search/Results",
            "summary": "Demo job returned because USAJOBS credentials are not configured.",
            "salary": {"MinimumRange": "50000", "MaximumRange": "75000", "RateIntervalCode": "Per Year"},
            "source": "demo",
        },
        {
            "id": "demo-usajobs-2",
            "title": f"Junior {clean_keyword.title()}",
            "organization": "Demo Public Service Lab",
            "department": "SkillBridge Demo",
            "location": "Remote",
            "apply_url": "https://www.usajobs.gov/Search/Results",
            "summary": "Use USAJOBS_EMAIL and USAJOBS_API_KEY for live federal job search.",
            "salary": {"MinimumRange": "45000", "MaximumRange": "68000", "RateIntervalCode": "Per Year"},
            "source": "demo",
        },
    ]

