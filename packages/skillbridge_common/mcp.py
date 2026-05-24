from __future__ import annotations

from typing import Any, Protocol


class MCPTool(Protocol):
    name: str

    async def call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class ToolUnavailableError(RuntimeError):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> MCPTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolUnavailableError(f"MCP tool is not registered: {name}") from exc

