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

    def __init__(self, routes: list[AgentRoute], source: str) -> None:
        self.routes = sorted(routes, key=lambda route: route.priority)
        self.source = source

    def select_route(self, intent_key: str, user_input: str) -> AgentRoute | None:
        for route in self.routes:
            if route.intent_key == intent_key and route.matches(user_input):
                return route
        return None


@lru_cache(maxsize=1)
def get_agent_hub_config() -> AgentHubConfig:
    """Load Agent Hub config from Supabase/PostgreSQL, falling back safely."""
    db_config = _load_from_database()
    if db_config:
        return db_config
    return AgentHubConfig(_fallback_routes(), source="fallback")


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
    return AgentHubConfig(routes, source="database") if routes else None


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
