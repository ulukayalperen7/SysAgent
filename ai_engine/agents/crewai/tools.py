"""CrewAI tool definitions for SysAgent read-only diagnostics."""

from typing import Callable, TypeVar

from agents.crewai.mcp_tool_wrappers import build_network_audit_report, build_system_audit_report

F = TypeVar("F", bound=Callable)

try:
    from crewai.tools import tool
except Exception:
    def tool(name: str) -> Callable[[F], F]:
        """Fallback decorator for import-limited test environments."""
        def decorator(func: F) -> F:
            setattr(func, "name", name)
            return func

        return decorator


@tool("System Audit Tool")
def system_audit_tool(query: str) -> str:
    """
    Inspect local processes through the SysAgent MCP read-only capability layer.

    This tool never closes, kills, or mutates processes. It returns top memory
    consumers and optional process-name matches for CrewAI diagnostics.
    """
    return build_system_audit_report(query)


@tool("Network Audit Tool")
def network_audit_tool(query: str) -> str:
    """
    Inspect active local network connections through MCP without mutation.

    This tool never sends packets, blocks connections, or changes firewall
    state. It only returns bounded connection facts for CrewAI diagnostics.
    """
    return build_network_audit_report(query)
