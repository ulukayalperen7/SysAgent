"""LangGraph node for MCP-backed read-only local inspection."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from core.agent_state import AgentState
from core.mcp_client import local_system_mcp_client

READ_ONLY_INTENTS = {"FILE_SYSTEM_READ", "DEVOPS_READ", "NETWORK_READ"}

DIAGNOSTIC_TERMS = {
    "why",
    "investigate",
    "diagnose",
    "analyze",
    "slow",
    "suspicious",
    "security",
    "leak",
    "problem",
    "issue",
}


def is_mcp_read_only_supported(state: AgentState) -> bool:
    """Return true when the current state should use MCP read-only tools."""
    intent = state.get("current_intent", "UNKNOWN")
    user_input = state.get("user_input", "")
    lower_input = user_input.lower()

    if intent in READ_ONLY_INTENTS:
        return True

    if intent == "SYSTEM_OPERATION":
        if any(term in lower_input for term in DIAGNOSTIC_TERMS):
            return False
        return _select_mcp_tool(user_input)[0] is not None

    return False


def mcp_read_only_node(state: AgentState) -> dict[str, Any]:
    """
    Execute supported safe read-only inspections through the MCP client facade.

    This node never executes shell commands and never returns approval-required
    scripts. Unsupported safe reads produce a concise clarification instead of
    falling back to shell execution.
    """
    user_input = state.get("user_input", "")
    tool_name, arguments = _select_mcp_tool(user_input)

    if not tool_name:
        explanation = (
            "Summary:\n"
            "I understood this as a read-only request, but I could not map it to a supported MCP inspection yet.\n\n"
            "Recommendation:\n"
            "Try asking for top memory processes, system metrics, network connections, a directory listing, or a specific file read."
        )
        return {"explanation": _append_explanation(state, explanation), "script": "NONE", "messages": [{"role": "ai", "content": explanation}]}

    result = local_system_mcp_client.call_tool(tool_name, arguments)
    explanation = _format_mcp_result(tool_name, result)

    return {
        "explanation": _append_explanation(state, explanation),
        "script": "NONE",
        "messages": [{"role": "ai", "content": explanation}],
        "errors": [] if result.get("success") else [result.get("error", "MCP read-only tool failed.")],
        "retry_count": 0,
    }


def _select_mcp_tool(user_input: str) -> tuple[str | None, dict[str, Any]]:
    lower_input = user_input.lower()

    if _looks_like_file_read(lower_input):
        path = _extract_path(user_input)
        if path:
            return "filesystem_read_file", {"path": path}
        return None, {}

    if _looks_like_directory_listing(lower_input):
        return "filesystem_list_directory", {"path": _extract_path(user_input)}

    if any(term in lower_input for term in ("network", "connection", "connections", "port", "ports", "socket")):
        return "network_list_connections", {"limit": _extract_limit(user_input, default=50, maximum=100)}

    if "top" in lower_input and any(term in lower_input for term in ("memory", "ram", "process", "processes")):
        return "system_get_top_memory_processes", {"limit": _extract_limit(user_input, default=10, maximum=50)}

    if any(term in lower_input for term in ("processes", "running process", "running apps", "tasks")):
        return "system_list_processes", {"query": _extract_process_query(user_input), "limit": _extract_limit(user_input, default=50, maximum=100)}

    if any(term in lower_input for term in ("cpu", "ram", "memory", "disk", "metrics", "usage", "load")):
        return "system_get_metrics_snapshot", {}

    if any(term in lower_input for term in ("platform", "os", "operating system", "system info", "machine info")):
        return "system_get_platform_info", {}

    return None, {}


def _looks_like_file_read(lower_input: str) -> bool:
    return any(term in lower_input for term in ("read file", "read this", "open file", "show file", "cat ", "log file", ".log", ".txt"))


def _looks_like_directory_listing(lower_input: str) -> bool:
    return any(term in lower_input for term in ("list files", "show files", "list directory", "show directory", "list folder", "show folder", "dir "))


def _extract_limit(text: str, default: int, maximum: int) -> int:
    match = re.search(r"\btop\s+(\d+)\b|\b(\d+)\s+(?:processes|files|connections|items)\b", text, re.IGNORECASE)
    if not match:
        return default
    value = int(next(group for group in match.groups() if group))
    return max(1, min(value, maximum))


def _extract_process_query(text: str) -> str | None:
    match = re.search(r"(?:named|called|for|matching)\s+['\"]?([A-Za-z0-9_. -]{2,60})['\"]?", text, re.IGNORECASE)
    if not match:
        return None
    query = match.group(1).strip(" .")
    return query or None


def _extract_path(text: str) -> str | None:
    quoted = re.search(r"['\"]([^'\"]+)['\"]", text)
    if quoted:
        return _normalize_user_path(quoted.group(1))

    windows_path = re.search(r"([A-Za-z]:\\[^\r\n]+)", text)
    if windows_path:
        return _normalize_user_path(windows_path.group(1).strip())

    home_path = re.search(r"(~[\\/][^\s]+|\$HOME[\\/][^\s]+|\$env:USERPROFILE[\\/][^\s]+)", text, re.IGNORECASE)
    if home_path:
        return _normalize_user_path(home_path.group(1).strip())

    lower_text = text.lower()
    if any(term in lower_text for term in ("this project", "current directory", "current folder", "this folder", "here")):
        return str(Path.cwd())

    common_locations = {
        "downloads": "Downloads",
        "download": "Downloads",
        "desktop": "Desktop",
        "documents": "Documents",
        "document": "Documents",
    }
    for key, folder in common_locations.items():
        if key in lower_text:
            return str(Path.home() / folder)

    path_after_preposition = re.search(r"(?:in|from|at|under|inside)\s+([^\r\n]+)$", text, re.IGNORECASE)
    if path_after_preposition:
        return _normalize_user_path(path_after_preposition.group(1).strip(" ."))

    return None


def _normalize_user_path(path_text: str) -> str:
    cleaned = path_text.strip().strip("'\"")
    cleaned = cleaned.replace("/", os.sep) if os.name == "nt" and not re.match(r"^[a-z]+:", cleaned, re.IGNORECASE) else cleaned
    return os.path.expandvars(os.path.expanduser(cleaned))


def _append_explanation(state: AgentState, explanation: str) -> str:
    current = state.get("explanation", "").strip()
    if not current:
        return explanation
    return f"{current}\n{explanation}".strip()


def _format_mcp_result(tool_name: str, result: dict[str, Any]) -> str:
    if not result.get("success"):
        return f"Summary:\nMCP read-only inspection failed.\n\nFindings:\n{result.get('error', 'Unknown error.')}\n\nRecommendation:\nCheck the path/request and try again."

    data = result.get("data", {})

    if tool_name == "system_get_top_memory_processes":
        lines = _format_process_rows(data.get("processes", []))
        return f"Summary:\nTop memory-consuming processes found.\n\nFindings:\n{lines}\n\nRecommendation:\nIf one process looks abnormal, ask me to investigate it before closing anything."

    if tool_name == "system_list_processes":
        lines = _format_process_rows(data.get("processes", []))
        return f"Summary:\nListed running processes with read-only MCP inspection.\n\nFindings:\n{lines}\n\nRecommendation:\nUse a process name if you want a narrower lookup."

    if tool_name == "network_list_connections":
        lines = _format_connection_rows(data.get("connections", []))
        return f"Summary:\nActive network connections inspected without changing network state.\n\nFindings:\n{lines}\n\nRecommendation:\nFlagged suspicious ports deserve deeper CrewAI diagnostics before any action."

    if tool_name == "filesystem_list_directory":
        lines = _format_directory_rows(data.get("entries", []))
        return f"Summary:\nDirectory listed successfully.\n\nFindings:\nPath: {data.get('path')}\n{lines}\n\nRecommendation:\nAsk me to read a specific file if you want details."

    if tool_name == "filesystem_read_file":
        content = str(data.get("content", ""))
        preview = content[:2000]
        truncated_note = "\n\nNote: Output was truncated." if data.get("truncated") else ""
        return f"Summary:\nFile read successfully.\n\nFindings:\nPath: {data.get('path')}\nSize: {data.get('size_bytes')} bytes\n\nContent Preview:\n{preview}{truncated_note}"

    if tool_name == "system_get_metrics_snapshot":
        return (
            "Summary:\nSystem metrics snapshot collected.\n\n"
            "Findings:\n"
            f"CPU: {data.get('cpu_percent')}%\n"
            f"RAM: {data.get('memory_percent')}% used\n"
            f"Disk: {data.get('disk_percent')}% used\n"
            f"Logical CPUs: {data.get('cpu_count_logical')}\n\n"
            "Recommendation:\nAsk for top memory or process details if usage looks high."
        )

    if tool_name == "system_get_platform_info":
        return (
            "Summary:\nPlatform information collected.\n\n"
            "Findings:\n"
            f"OS: {data.get('system')} {data.get('release')}\n"
            f"Machine: {data.get('machine')}\n"
            f"Hostname: {data.get('hostname')}\n"
            f"Python: {data.get('python_version')}"
        )

    return f"Summary:\nMCP read-only inspection completed.\n\nFindings:\n{data}"


def _format_process_rows(processes: list[dict[str, Any]]) -> str:
    if not processes:
        return "No matching processes found."

    rows = []
    for process in processes[:15]:
        rows.append(
            f"- PID {process.get('pid')} | {process.get('name')} | RAM {process.get('memory_mb')} MB | CPU {process.get('cpu_percent')}%"
        )
    return "\n".join(rows)


def _format_connection_rows(connections: list[dict[str, Any]]) -> str:
    if not connections:
        return "No network connections found."

    rows = []
    for conn in connections[:15]:
        flag = " | suspicious port" if conn.get("suspicious_port") else ""
        rows.append(
            f"- {conn.get('process')} PID {conn.get('pid')} | {conn.get('local_ip')}:{conn.get('local_port')} -> "
            f"{conn.get('remote_ip')}:{conn.get('remote_port')} | {conn.get('status')}{flag}"
        )
    return "\n".join(rows)


def _format_directory_rows(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "Directory is empty or no entries were available."

    rows = []
    for entry in entries[:30]:
        size = f" | {entry.get('size_bytes')} bytes" if entry.get("size_bytes") is not None else ""
        rows.append(f"- {entry.get('type')}: {entry.get('name')}{size}")
    return "\n".join(rows)
