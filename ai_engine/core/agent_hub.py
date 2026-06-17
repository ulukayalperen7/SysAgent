"""Agent Hub runtime configuration for LangGraph routing.

The database-backed path is optional on purpose: SysAgent must keep working on
developer machines before Supabase/Auth is fully wired. When the database or
driver is unavailable, this module returns the same safe defaults seeded by the
Phase 6 migration.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from core.config import settings


@dataclass(frozen=True)
class AgentRoute:
    """A DB-configurable route from an intent to a LangGraph node."""

    intent_key: str
    priority: int
    route_type: str
    target_langgraph_node: str
    approval_policy: str
    matcher: dict[str, Any]

    def matches(self, user_input: str) -> bool:
        diagnostic_terms = self.matcher.get("diagnostic_terms")
        if diagnostic_terms:
            lower_input = user_input.lower()
            return any(str(term).lower() in lower_input for term in diagnostic_terms)
        return True


class AgentHubConfig:
    """In-memory view of Agent Hub route configuration."""

    def __init__(
        self,
        routes: list[AgentRoute],
        source: str,
        mcp_tool_permissions: dict[str, set[str]] | None = None,
    ) -> None:
        self.routes = sorted(routes, key=lambda route: route.priority)
        self.source = source
        self.mcp_tool_permissions = mcp_tool_permissions or {}

    def select_route(self, intent_key: str, user_input: str) -> AgentRoute | None:
        for route in self.routes:
            if route.intent_key == intent_key and route.matches(user_input):
                return route
        return None

    def is_mcp_tool_allowed(self, agent_slug: str, tool_name: str) -> bool:
        allowed_tools = self.mcp_tool_permissions.get(agent_slug)
        if allowed_tools is None:
            return False
        return tool_name in allowed_tools

    def to_dict(self) -> dict[str, Any]:
        """Return a safe diagnostics view for API status endpoints."""
        return {
            "source": self.source,
            "route_count": len(self.routes),
            "routes": [
                {
                    "intent_key": route.intent_key,
                    "priority": route.priority,
                    "route_type": route.route_type,
                    "target_langgraph_node": route.target_langgraph_node,
                    "approval_policy": route.approval_policy,
                    "matcher": route.matcher,
                }
                for route in self.routes
            ],
            "mcp_tool_permissions": {
                agent_slug: sorted(tool_names)
                for agent_slug, tool_names in self.mcp_tool_permissions.items()
            },
        }


@lru_cache(maxsize=1)
def get_agent_hub_config() -> AgentHubConfig:
    """Load Agent Hub config from Supabase/PostgreSQL, falling back safely."""
    db_config = _load_from_database()
    if db_config:
        return db_config
    return AgentHubConfig(
        _fallback_routes(),
        source="fallback",
        mcp_tool_permissions=_fallback_mcp_tool_permissions(),
    )


def reload_agent_hub_config() -> AgentHubConfig:
    """Clear the cached config and load it again."""
    get_agent_hub_config.cache_clear()
    return get_agent_hub_config()


def _load_from_database() -> AgentHubConfig | None:
    database_url = settings.database_url.strip()
    if not database_url or database_url.startswith("jdbc:"):
        return None

    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        return None

    sql = """
        select
            r.intent_key,
            r.priority,
            r.route_type,
            r.target_langgraph_node,
            r.approval_policy,
            r.matcher
        from agent_intent_routes r
        left join agent_profiles a on a.id = r.target_agent_id
        where r.enabled = true
          and (a.id is null or a.status = 'active')
        order by r.priority asc
    """

    try:
        with psycopg.connect(database_url, row_factory=dict_row, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                cur.execute(
                    """
                    select a.slug as agent_slug, t.name as tool_name
                    from agent_mcp_tool_permissions p
                    join agent_profiles a on a.id = p.agent_id
                    join mcp_tools t on t.id = p.mcp_tool_id
                    where a.status = 'active'
                      and t.enabled = true
                      and p.permission_mode = 'allow'
                    """
                )
                permission_rows = cur.fetchall()
    except Exception:
        return None

    routes = [
        AgentRoute(
            intent_key=str(row["intent_key"]),
            priority=int(row["priority"]),
            route_type=str(row["route_type"]),
            target_langgraph_node=str(row["target_langgraph_node"]),
            approval_policy=str(row["approval_policy"]),
            matcher=row["matcher"] if isinstance(row["matcher"], dict) else {},
        )
        for row in rows
        if row.get("target_langgraph_node")
    ]
    permissions: dict[str, set[str]] = {}
    for row in permission_rows:
        permissions.setdefault(str(row["agent_slug"]), set()).add(str(row["tool_name"]))

    return AgentHubConfig(routes, source="database", mcp_tool_permissions=permissions) if routes else None


def _fallback_routes() -> list[AgentRoute]:
    return [
        AgentRoute("CHAT", 10, "chat", "direct_chat_node", "none", {}),
        AgentRoute("FILE_SYSTEM_READ", 20, "mcp_read_only", "mcp_read_only_node", "none", {}),
        AgentRoute("DEVOPS_READ", 20, "mcp_read_only", "mcp_read_only_node", "none", {}),
        AgentRoute("NETWORK_READ", 20, "mcp_read_only", "mcp_read_only_node", "none", {}),
        AgentRoute(
            "SYSTEM_OPERATION",
            30,
            "crewai_diagnostics",
            "run_crewai_diagnostics_node",
            "risk_based",
            {
                "diagnostic_terms": [
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
                ]
            },
        ),
        AgentRoute("FILE_SYSTEM_WRITE", 90, "script_proposal", "generate_action_script_node", "always", {}),
        AgentRoute("APP_CONTROL", 90, "script_proposal", "generate_action_script_node", "always", {}),
        AgentRoute("DEVOPS_WRITE", 90, "script_proposal", "generate_action_script_node", "always", {}),
        AgentRoute("UNKNOWN", 90, "script_proposal", "generate_action_script_node", "always", {}),
    ]


def _fallback_mcp_tool_permissions() -> dict[str, set[str]]:
    return {
        "mcp_read_agent": {
            "system_get_metrics_snapshot",
            "system_list_processes",
            "system_get_top_memory_processes",
            "network_list_connections",
            "filesystem_list_directory",
            "filesystem_read_file",
            "system_get_platform_info",
        },
        "crewai_diagnostics_agent": {
            "system_get_metrics_snapshot",
            "system_list_processes",
            "system_get_top_memory_processes",
            "network_list_connections",
            "system_get_platform_info",
        },
    }
