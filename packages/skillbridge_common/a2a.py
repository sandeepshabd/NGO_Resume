from __future__ import annotations

import json
import os

import httpx

from skillbridge_common.schemas import AgentCard, TaskRequest, TaskResponse


class AgentRegistry:
    def __init__(self, cards: list[AgentCard]) -> None:
        self._cards = {card.name: card for card in cards}

    @classmethod
    def from_env(cls) -> "AgentRegistry":
        raw = os.getenv("AGENT_REGISTRY_JSON", "[]")
        cards = [AgentCard.model_validate(item) for item in json.loads(raw)]
        return cls(cards)

    def all_cards(self) -> list[AgentCard]:
        return list(self._cards.values())

    def find_by_skill(self, skill_id: str) -> AgentCard | None:
        for card in self._cards.values():
            if any(skill.id == skill_id for skill in card.skills):
                return card
        return None


class A2AClient:
    def __init__(self, token: str | None = None, timeout_seconds: float = 30.0) -> None:
        self._token = token or os.getenv("SKILLBRIDGE_AGENT_TOKEN")
        self._timeout_seconds = timeout_seconds

    async def send_task(self, card: AgentCard, request: TaskRequest) -> TaskResponse:
        headers = {}
        if self._token:
            headers["x-skillbridge-agent-token"] = self._token
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{card.url.rstrip('/')}/tasks",
                json=request.model_dump(mode="json"),
                headers=headers,
            )
            response.raise_for_status()
            return TaskResponse.model_validate(response.json())

