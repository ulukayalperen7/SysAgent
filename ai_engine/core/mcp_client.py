"""MCP client wrapper for SysAgent read-only tools.

The preferred path is a real MCP client/server transport. A direct in-process
fallback remains so the product still runs when the MCP SDK or server process is
not available on a developer machine.
"""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Awaitable

from core.config import settings
from core.mcp_process import ensure_local_mcp_server
from mcp_servers.local_system_tools import TOOL_REGISTRY, list_tool_names


@dataclass(frozen=True)
class McpClientStatus:
    """Current local MCP client mode."""

    available: bool
    mode: str
    detail: str


class LocalSystemMcpClient:
    """
    Read-only MCP client for LangGraph and CrewAI integrations.

    In normal local runs this talks to the local MCP server over streamable HTTP
    on the configured port. If transport is unavailable, it falls back to the
    same read-only implementations in-process.
    """

    def __init__(self) -> None:
        self._tools = TOOL_REGISTRY

    def status(self) -> McpClientStatus:
        if settings.mcp_prefer_transport:
            try:
                ensure_local_mcp_server()
                self._list_tools_transport()
                return McpClientStatus(
                    available=True,
                    mode="mcp_streamable_http",
                    detail=f"Connected to local MCP server at {self._server_url()}",
                )
            except Exception as exc:
                return McpClientStatus(
                    available=True,
                    mode="in_process_read_only_fallback",
                    detail=f"MCP transport unavailable ({exc}); using local read-only fallback.",
                )

        return McpClientStatus(
            available=True,
            mode="in_process_read_only",
            detail="Using local read-only MCP tool implementations directly.",
        )

    def list_tools(self) -> list[str]:
        if settings.mcp_prefer_transport:
            try:
                ensure_local_mcp_server()
                return self._list_tools_transport()
            except Exception:
                pass
        return list_tool_names()

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if settings.mcp_prefer_transport:
            try:
                ensure_local_mcp_server()
                return self._call_tool_transport(name, arguments or {})
            except Exception:
                pass
        return self._call_tool_in_process(name, arguments)

    def _call_tool_in_process(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if name not in self._tools:
            return {
                "success": False,
                "error": f"Unknown MCP tool: {name}",
                "available_tools": list_tool_names(),
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

    def _list_tools_transport(self) -> list[str]:
        return _run_async_from_sync(self._list_tools_transport_async())

    def _call_tool_transport(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return _run_async_from_sync(self._call_tool_transport_async(name, arguments))

    async def _list_tools_transport_async(self) -> list[str]:
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
            import httpx
        except ImportError as exc:
            raise RuntimeError("MCP Python SDK is not installed") from exc

        async with httpx.AsyncClient(timeout=settings.mcp_connect_timeout_seconds) as http_client:
            async with streamable_http_client(
                self._server_url(),
                http_client=http_client,
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return sorted(tool.name for tool in result.tools)

    async def _call_tool_transport_async(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
            import httpx
        except ImportError as exc:
            raise RuntimeError("MCP Python SDK is not installed") from exc

        async with httpx.AsyncClient(timeout=settings.mcp_connect_timeout_seconds) as http_client:
            async with streamable_http_client(
                self._server_url(),
                http_client=http_client,
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(name, arguments)
                    return _normalize_call_result(result)

    def _server_url(self) -> str:
        path = settings.mcp_path if settings.mcp_path.startswith("/") else f"/{settings.mcp_path}"
        return f"http://{settings.mcp_host}:{settings.mcp_port}{path}"


def _run_async_from_sync(awaitable: Awaitable[Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(lambda: asyncio.run(awaitable)).result()


def _normalize_call_result(result: Any) -> dict[str, Any]:
    is_error = bool(getattr(result, "isError", False) or getattr(result, "is_error", False))
    structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured if not is_error else {"success": False, "error": str(structured)}

    content = getattr(result, "content", None) or []
    texts: list[str] = []
    for item in content:
        text = getattr(item, "text", None)
        if text is not None:
            texts.append(text)

    if texts:
        joined = "\n".join(texts)
        try:
            parsed = json.loads(joined)
            if isinstance(parsed, dict):
                return parsed if not is_error else {"success": False, "error": parsed.get("error", joined)}
        except json.JSONDecodeError:
            pass
        return {"success": not is_error, "data": joined} if not is_error else {"success": False, "error": joined}

    return {"success": not is_error, "data": None} if not is_error else {"success": False, "error": "MCP tool returned an error."}


local_system_mcp_client = LocalSystemMcpClient()
