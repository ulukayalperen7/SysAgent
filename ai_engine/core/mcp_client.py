"""Graceful client wrapper for SysAgent MCP read-only tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mcp_servers.local_system_tools import TOOL_REGISTRY, list_tool_names


@dataclass(frozen=True)
class McpClientStatus:
    """Current local MCP client mode."""

    available: bool
    mode: str
    detail: str


class LocalSystemMcpClient:
    """
    Stable read-only MCP tool facade for LangGraph and CrewAI integrations.

    Phase 1 keeps calls in-process so the AI Engine can start even when the
    optional MCP SDK or an external MCP server transport is unavailable. The
    public tool names mirror the local MCP server and can later be backed by
    stdio or HTTP transport without changing LangGraph node code.
    """

    def __init__(self) -> None:
        self._tools = TOOL_REGISTRY

    def status(self) -> McpClientStatus:
        return McpClientStatus(
            available=True,
            mode="in_process_read_only",
            detail="Using local read-only MCP tool implementations directly.",
        )

    def list_tools(self) -> list[str]:
        return list_tool_names()

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if name not in self._tools:
            return {
                "success": False,
                "error": f"Unknown MCP tool: {name}",
                "available_tools": self.list_tools(),
            }

        tool = self._tools[name]
        tool_args = arguments or {}

        try:
            result = tool(**tool_args)
        except TypeError as exc:
            return {"success": False, "error": f"Invalid arguments for MCP tool '{name}': {exc}"}
        except Exception as exc:
            return {"success": False, "error": f"MCP tool '{name}' failed: {exc}"}

        if isinstance(result, dict):
            return result
        return {"success": True, "data": result}


local_system_mcp_client = LocalSystemMcpClient()

