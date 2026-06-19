"""LangGraph node for MCP-backed read-only local inspection."""

from __future__ import annotations

from typing import Any

from core.agent_state import AgentState
from core.agent_hub import get_agent_hub_config
from core.mcp_client import local_system_mcp_client
from core.mcp_tool_planner import plan_mcp_read_tool

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
        return plan_mcp_read_tool(user_input, intent) is not None

    return False


def mcp_read_only_node(state: AgentState) -> dict[str, Any]:
    """
    Execute supported safe read-only inspections through the MCP client facade.

    This node never executes shell commands and never returns approval-required
    scripts. Unsupported safe reads produce a concise clarification instead of
    falling back to shell execution.
    """
    user_input = state.get("user_input", "")
    intent = state.get("current_intent", "UNKNOWN")
    plan = plan_mcp_read_tool(user_input, intent)

    if not plan:
        explanation = (
            "Summary:\n"
            "I understood this as a read-only request, but I could not map it to a supported MCP inspection yet.\n\n"
            "Recommendation:\n"
            "Try asking for top memory processes, system metrics, network connections, a directory listing, or a specific file read."
        )
        return {"explanation": _append_explanation(state, explanation), "script": "NONE", "messages": [{"role": "ai", "content": explanation}]}

    if not get_agent_hub_config().is_mcp_tool_allowed("mcp_read_agent", plan.tool_name):
        explanation = (
            "Summary:\n"
            "This read-only inspection is not enabled for the current Agent Hub policy.\n\n"
            "Recommendation:\n"
            "Enable the MCP tool permission for this agent if this capability should be available."
        )
        return {"explanation": _append_explanation(state, explanation), "script": "NONE", "messages": [{"role": "ai", "content": explanation}]}

    result = local_system_mcp_client.call_tool(plan.tool_name, plan.arguments)
    explanation = _format_mcp_result(plan.tool_name, result)

    return {
        "explanation": _append_explanation(state, explanation),
        "script": "NONE",
        "messages": [{"role": "ai", "content": explanation}],
        "mcp_tools_used": [plan.tool_name],
        "errors": [] if result.get("success") else [result.get("error", "MCP read-only tool failed.")],
        "retry_count": 0,
    }


def _append_explanation(state: AgentState, explanation: str) -> str:
    current = state.get("explanation", "").strip()
    if not current:
        return explanation
    return f"{current}\n{explanation}".strip()


def _format_mcp_result(tool_name: str, result: dict[str, Any]) -> str:
    if not result.get("success"):
        return f"Summary:\nMCP read-only inspection failed.\n\nFindings:\n{result.get('error', 'Unknown error.')}\n\nRecommendation:\nCheck the path/request and try again."

    data = result.get("data", {})

    if tool_name == "devops_git_status":
        changes = data.get("changes", [])
        change_lines = "\n".join(f"- {change}" for change in changes[:30]) if changes else "No working tree changes."
        return (
            "Summary:\nGit status inspected without changing the repository.\n\n"
            "Findings:\n"
            f"Path: {data.get('path')}\n"
            f"Branch: {data.get('branch')}\n"
            f"Clean: {data.get('clean')}\n"
            f"{change_lines}"
        )

    if tool_name == "devops_docker_ps":
        containers = data.get("containers", [])
        lines = "\n".join(
            f"- {container.get('Names') or container.get('raw')} | {container.get('Image')} | {container.get('Status')}"
            for container in containers[:20]
        ) if containers else "No running containers found."
        return f"Summary:\nDocker containers inspected without mutation.\n\nFindings:\n{lines}"

    if tool_name == "devops_list_npm_scripts":
        scripts = data.get("scripts", {})
        lines = "\n".join(f"- {name}: {command}" for name, command in list(scripts.items())[:30]) if scripts else "No npm scripts found."
        return (
            "Summary:\npackage.json scripts inspected without running npm.\n\n"
            "Findings:\n"
            f"Path: {data.get('path')}\n"
            f"Package: {data.get('name')}\n"
            f"{lines}"
        )

    if tool_name == "system_get_top_memory_processes":
        lines = _format_process_rows(data.get("processes", []))
        return f"Summary:\nTop memory-consuming processes found.\n\nFindings:\n{lines}\n\nRecommendation:\nIf one process looks abnormal, ask me to investigate it before closing anything."

    if tool_name == "system_list_processes":
        lines = _format_process_rows(data.get("processes", []))
        return f"Summary:\nListed running processes with read-only MCP inspection.\n\nFindings:\n{lines}\n\nRecommendation:\nUse a process name if you want a narrower lookup."

    if tool_name == "network_list_connections":
        lines = _format_connection_rows(data.get("connections", []))
        return f"Summary:\nActive network connections inspected without changing network state.\n\nFindings:\n{lines}\n\nRecommendation:\nFlagged suspicious ports deserve deeper CrewAI diagnostics before any action."

    if tool_name == "network_list_interfaces":
        lines = _format_interface_rows(data.get("interfaces", []))
        return f"Summary:\nNetwork interfaces inspected without changing network state.\n\nFindings:\n{lines}"

    if tool_name == "system_get_disk_partitions":
        lines = _format_partition_rows(data.get("partitions", []))
        return f"Summary:\nDisk partitions inspected without changing disk state.\n\nFindings:\n{lines}"

    if tool_name == "filesystem_list_directory":
        lines = _format_directory_rows(data.get("entries", []))
        return f"Summary:\nDirectory listed successfully.\n\nFindings:\nPath: {data.get('path')}\n{lines}\n\nRecommendation:\nAsk me to read a specific file if you want details."

    if tool_name == "filesystem_read_file":
        content = str(data.get("content", ""))
        preview = content[:2000]
        truncated_note = "\n\nNote: Output was truncated." if data.get("truncated") else ""
        return f"Summary:\nFile read successfully.\n\nFindings:\nPath: {data.get('path')}\nSize: {data.get('size_bytes')} bytes\n\nContent Preview:\n{preview}{truncated_note}"

    if tool_name == "filesystem_search":
        lines = _format_search_rows(data.get("matches", []))
        truncated_note = "\n\nNote: Search output was truncated." if data.get("truncated") else ""
        return (
            "Summary:\nFilesystem search completed.\n\n"
            "Findings:\n"
            f"Path: {data.get('path')}\n"
            f"Pattern: {data.get('pattern')}\n"
            f"Matches: {data.get('count')}\n"
            f"{lines}{truncated_note}"
        )

    if tool_name == "filesystem_get_disk_usage":
        total_bytes = int(data.get("total_bytes") or 0)
        return (
            "Summary:\nDisk usage scan completed.\n\n"
            "Findings:\n"
            f"Path: {data.get('path')}\n"
            f"Total: {_format_bytes(total_bytes)}\n"
            f"Files: {data.get('file_count')}\n"
            f"Directories: {data.get('directory_count')}\n"
            f"Truncated: {data.get('truncated')}"
        )

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


def _format_interface_rows(interfaces: list[dict[str, Any]]) -> str:
    if not interfaces:
        return "No network interfaces found."

    rows = []
    for interface in interfaces[:15]:
        addresses = []
        for address in interface.get("addresses", [])[:4]:
            if address.get("address"):
                addresses.append(f"{address.get('family')}={address.get('address')}")
        address_text = ", ".join(addresses) if addresses else "no addresses"
        rows.append(
            f"- {interface.get('name')} | up={interface.get('is_up')} | "
            f"speed={interface.get('speed_mbps')} Mbps | {address_text}"
        )
    return "\n".join(rows)


def _format_partition_rows(partitions: list[dict[str, Any]]) -> str:
    if not partitions:
        return "No disk partitions found."

    rows = []
    for partition in partitions[:15]:
        usage = partition.get("usage") or {}
        usage_text = (
            f" | used={usage.get('percent')}% | free={_format_bytes(int(usage.get('free_bytes') or 0))}"
            if usage
            else " | usage unavailable"
        )
        rows.append(
            f"- {partition.get('device')} -> {partition.get('mountpoint')} | "
            f"{partition.get('fstype')}{usage_text}"
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


def _format_search_rows(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return "No matching files or directories found."

    rows = []
    for match in matches[:30]:
        size = f" | {match.get('size_bytes')} bytes" if match.get("size_bytes") is not None else ""
        rows.append(f"- {match.get('type')}: {match.get('path')}{size}")
    return "\n".join(rows)


def _format_bytes(value: int) -> str:
    units = ["bytes", "KB", "MB", "GB", "TB"]
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.2f} {unit}" if unit != "bytes" else f"{int(amount)} bytes"
        amount /= 1024
    return f"{value} bytes"
