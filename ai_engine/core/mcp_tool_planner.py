"""Intent-aware MCP read-only tool planner.

This module keeps tool selection out of LangGraph node code. The first version
is deterministic by design: it produces a small, auditable plan for read-only
MCP tools without granting an LLM direct tool selection authority.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

READ_COMPATIBLE_INTENTS = {"FILE_SYSTEM_READ", "DEVOPS_READ", "NETWORK_READ", "SYSTEM_OPERATION"}


@dataclass(frozen=True)
class McpToolPlan:
    """A selected read-only MCP tool call."""

    tool_name: str
    arguments: dict[str, Any]
    confidence: float
    reason: str


def plan_mcp_read_tool(user_input: str, intent: str) -> McpToolPlan | None:
    """Return the best read-only MCP tool plan for the current terminal step."""
    if intent not in READ_COMPATIBLE_INTENTS:
        return None

    normalized = _normalize_for_matching(user_input)

    if _looks_like_filesystem_search(normalized):
        return McpToolPlan(
            "filesystem_search",
            {
                "path": _extract_path(user_input),
                "pattern": _extract_search_pattern(user_input),
                "limit": _extract_limit(user_input, default=30, maximum=100),
            },
            0.88,
            "The request asks to find or search for files.",
        )

    if _looks_like_file_read(normalized):
        path = _extract_path(user_input)
        if path:
            return McpToolPlan(
                "filesystem_read_file",
                {"path": path},
                0.9,
                "The request asks to read or show a specific file.",
            )
        return None

    if _looks_like_disk_usage(normalized):
        return McpToolPlan(
            "filesystem_get_disk_usage",
            {"path": _extract_path(user_input)},
            0.85,
            "The request asks for folder or disk usage.",
        )

    if _looks_like_directory_listing(normalized):
        return McpToolPlan(
            "filesystem_list_directory",
            {"path": _extract_path(user_input)},
            0.86,
            "The request asks to list files or folders.",
        )

    if any(term in normalized for term in ("network", "connection", "connections", "port", "ports", "socket")):
        return McpToolPlan(
            "network_list_connections",
            {"limit": _extract_limit(user_input, default=50, maximum=100)},
            0.84,
            "The request asks for network connection information.",
        )

    if "top" in normalized and any(term in normalized for term in ("memory", "ram", "process", "processes")):
        return McpToolPlan(
            "system_get_top_memory_processes",
            {"limit": _extract_limit(user_input, default=10, maximum=50)},
            0.9,
            "The request asks for top memory-consuming processes.",
        )

    if any(term in normalized for term in ("processes", "running process", "running apps", "tasks")):
        return McpToolPlan(
            "system_list_processes",
            {"query": _extract_process_query(user_input), "limit": _extract_limit(user_input, default=50, maximum=100)},
            0.83,
            "The request asks to inspect running processes.",
        )

    if any(term in normalized for term in ("cpu", "ram", "memory", "disk", "metrics", "usage", "load")):
        return McpToolPlan(
            "system_get_metrics_snapshot",
            {},
            0.78,
            "The request asks for system metrics.",
        )

    if any(term in normalized for term in ("platform", "os", "operating system", "system info", "machine info")):
        return McpToolPlan(
            "system_get_platform_info",
            {},
            0.8,
            "The request asks for platform information.",
        )

    return None


def _looks_like_file_read(normalized: str) -> bool:
    return any(term in normalized for term in ("read file", "read this", "open file", "show file", "cat ", "log file", ".log", ".txt"))


def _looks_like_directory_listing(normalized: str) -> bool:
    return any(term in normalized for term in ("list files", "show files", "list directory", "show directory", "list folder", "show folder", "dir "))


def _looks_like_filesystem_search(normalized: str) -> bool:
    return any(term in normalized for term in ("find file", "search file", "search for", "find files", "dosya ara", "dosya bul"))


def _looks_like_disk_usage(normalized: str) -> bool:
    return any(term in normalized for term in ("disk usage", "folder size", "directory size", "how big", "size of folder", "klasor boyutu", "disk kullanimi"))


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


def _extract_search_pattern(text: str) -> str:
    quoted = re.search(r"['\"]([^'\"]+)['\"]", text)
    if quoted:
        return quoted.group(1).strip() or "*"

    wildcard = re.search(r"(?<![\w.-])([A-Za-z0-9_*?.-]+\.[A-Za-z0-9_*?]{1,12})(?![\w.-])", text)
    if wildcard:
        return wildcard.group(1).strip()

    named = re.search(r"(?:named|called|for|matching)\s+([A-Za-z0-9_*?. -]{2,80})", text, re.IGNORECASE)
    if named:
        candidate = named.group(1).strip(" .")
        candidate = re.split(r"\s+(?:in|from|under|inside)\b", candidate, maxsplit=1, flags=re.IGNORECASE)[0].strip(" .")
        return candidate or "*"

    return "*"


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


def _normalize_for_matching(text: str) -> str:
    translation = str.maketrans(
        {
            "\u00e7": "c",
            "\u011f": "g",
            "\u0131": "i",
            "\u00f6": "o",
            "\u015f": "s",
            "\u00fc": "u",
            "\u00c7": "c",
            "\u011e": "g",
            "\u0130": "i",
            "\u00d6": "o",
            "\u015e": "s",
            "\u00dc": "u",
        }
    )
    return text.translate(translation).lower()
