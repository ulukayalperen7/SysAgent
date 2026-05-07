"""CrewAI-compatible report builders backed by SysAgent MCP read-only tools."""

from __future__ import annotations

from typing import Any

from core.mcp_client import local_system_mcp_client


def build_system_audit_report(query: str | None = None) -> str:
    """
    Return the process report CrewAI expects, using MCP tools underneath.

    The report stays plain text because CrewAI consumes tool output as context
    for subsequent security and reporting tasks.
    """
    search_query = _clean_query(query)
    top_result = local_system_mcp_client.call_tool("system_get_top_memory_processes", {"limit": 10})

    if not top_result.get("success"):
        return f"System audit failed: {top_result.get('error', 'Unknown MCP error')}"

    top_processes = top_result.get("data", {}).get("processes", [])
    report = "TOP 10 PROCESSES BY RAM USAGE:\n"
    report += _format_processes(top_processes)

    if search_query:
        match_result = local_system_mcp_client.call_tool(
            "system_list_processes",
            {"query": search_query, "limit": 10},
        )
        if match_result.get("success"):
            matches = match_result.get("data", {}).get("processes", [])
            if matches:
                report += f"\nMATCHES FOR SEARCH '{search_query}':\n"
                report += _format_processes(matches[:5])
            else:
                report += f"\nNO PROCESSES FOUND MATCHING '{search_query}'.\n"
        else:
            report += f"\nPROCESS SEARCH FAILED FOR '{search_query}': {match_result.get('error', 'Unknown MCP error')}\n"

    return report


def build_network_audit_report(query: str | None = None) -> str:
    """Return a CrewAI-compatible network report using MCP read-only tools."""
    result = local_system_mcp_client.call_tool("network_list_connections", {"limit": 50})

    if not result.get("success"):
        return f"Network audit failed: {result.get('error', 'Unknown MCP error')}"

    connections = result.get("data", {}).get("connections", [])
    active_connections = [
        conn for conn in connections if str(conn.get("status", "")).upper() == "ESTABLISHED"
    ]

    if not active_connections:
        return "No active ESTABLISHED connections found at this moment."

    query_text = _clean_query(query)
    if query_text:
        filtered = [
            conn
            for conn in active_connections
            if query_text in str(conn.get("process", "")).lower()
            or query_text in str(conn.get("remote_ip", "")).lower()
            or query_text in str(conn.get("remote_port", "")).lower()
            or query_text in str(conn.get("local_port", "")).lower()
        ]
        active_connections = filtered or active_connections

    report = f"ACTIVE NETWORK CONNECTIONS ({len(active_connections)} total):\n"
    for conn in active_connections[:15]:
        flag = " [SUSPICIOUS PORT]" if conn.get("suspicious_port") else ""
        remote_ip = conn.get("remote_ip") or "N/A"
        remote_port = conn.get("remote_port") or 0
        local_port = conn.get("local_port") or 0
        report += (
            f"Process: {conn.get('process')} (PID {conn.get('pid')}) | "
            f"Local Port: {local_port} -> "
            f"Remote: {remote_ip}:{remote_port}{flag}\n"
        )

    return report


def _clean_query(query: str | None) -> str | None:
    if not query:
        return None
    cleaned = query.strip()
    if not cleaned or cleaned.lower() == "none":
        return None
    return cleaned.lower()


def _format_processes(processes: list[dict[str, Any]]) -> str:
    if not processes:
        return "No process data available.\n"

    lines = []
    for process in processes:
        lines.append(
            f"PID: {process.get('pid')} | "
            f"Name: {process.get('name')} | "
            f"RAM: {process.get('memory_mb')} MB | "
            f"CPU: {process.get('cpu_percent')}%"
        )
    return "\n".join(lines) + "\n"

