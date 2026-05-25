from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class LLMClient(Protocol):
    async def complete_json(self, system: str, user: str) -> dict:
        ...


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    enabled: bool

    @classmethod
    def from_env(cls) -> "LLMSettings":
        return cls(
            provider=os.getenv("LLM_PROVIDER", "disabled"),
            model=os.getenv("VERTEX_MODEL", "gemini-1.5-flash"),
            enabled=os.getenv("ENABLE_LLM_CALLS", "false").lower() == "true",
        )


class DisabledLLMClient:
    async def complete_json(self, system: str, user: str) -> dict:
        return {
            "provider": "disabled",
            "model": "none",
            "system_prompt_length": len(system),
            "user_prompt_length": len(user),
            "note": "LLM calls are disabled for this low-cost POC runtime.",
        }


def get_llm_client(settings: LLMSettings | None = None) -> LLMClient:
    active_settings = settings or LLMSettings.from_env()
    if not active_settings.enabled:
        return DisabledLLMClient()

    # Vertex/Gemini integration belongs behind this interface. Keeping the import out of the
    # default path lets the POC run cheaply without adding model credentials or SDK setup.
    return DisabledLLMClient()

