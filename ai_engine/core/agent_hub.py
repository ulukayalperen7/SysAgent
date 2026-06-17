"""Agent Hub runtime configuration for LangGraph routing.

The database-backed path is optional on purpose: SysAgent must keep working on
developer machines before Supabase/Auth is fully wired. When the database or
driver is unavailable, this module returns the same safe defaults seeded by the
Phase 6 migration.
"""

from __future__ import annotations

import re
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


@dataclass(frozen=True)
class AgentRiskRule:
    """A DB-configurable safety rule for command blocking or approval gates."""

    rule_type: str
    pattern: str
    effect: str
    risk_level: str
    reason: str
    priority: int

    def blocks_command(self, command: str, os_name: str) -> bool:
        if self.effect != "block":
            return False

        command_lower = command.lower()
        pattern_lower = self.pattern.lower()

        if self.rule_type == "command_contains":
            return pattern_lower in command_lower

        if self.rule_type == "path_prefix":
            is_windows = "windows" in os_name.lower()
            if is_windows:
                return pattern_lower in command_lower
            return f" {pattern_lower}" in command_lower or command_lower.startswith(pattern_lower)

        if self.rule_type == "regex":
            try:
                return re.search(self.pattern, command, re.IGNORECASE) is not None
            except re.error:
                return False

        return False

    def requires_approval_for_intent(self, intent: str) -> bool:
        return (
            self.rule_type == "intent_key"
            and self.effect == "require_approval"
            and self.pattern.upper() == intent.upper()
        )


class AgentHubConfig:
    """In-memory view of Agent Hub route configuration."""

    def __init__(
        self,
        routes: list[AgentRoute],
        source: str,
        mcp_tool_permissions: dict[str, set[str]] | None = None,
        risk_rules: list[AgentRiskRule] | None = None,
    ) -> None:
        self.routes = sorted(routes, key=lambda route: route.priority)
        self.source = source
        self.mcp_tool_permissions = mcp_tool_permissions or {}
        self.risk_rules = sorted(risk_rules or [], key=lambda rule: rule.priority)

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

    def command_block_reason(self, command: str, os_name: str) -> str | None:
        for rule in self.risk_rules:
            if rule.blocks_command(command, os_name):
                return rule.reason
        return None

    def requires_approval(self, intent: str) -> bool | None:
        for rule in self.risk_rules:
            if rule.requires_approval_for_intent(intent):
                return True
        return None

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
            "risk_rule_count": len(self.risk_rules),
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
        risk_rules=_fallback_risk_rules(),
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
                cur.execute(
                    """
                    select
                        r.rule_type,
                        r.pattern,
                        r.effect,
                        r.risk_level,
                        r.reason,
                        r.priority
                    from agent_risk_policy_rules r
                    join agent_risk_policies p on p.id = r.policy_id
                    where p.enabled = true
                      and r.enabled = true
                    order by r.priority asc
                    """
                )
                risk_rows = cur.fetchall()
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

    risk_rules = [
        AgentRiskRule(
            rule_type=str(row["rule_type"]),
            pattern=str(row["pattern"]),
            effect=str(row["effect"]),
            risk_level=str(row["risk_level"]),
            reason=str(row["reason"]),
            priority=int(row["priority"]),
        )
        for row in risk_rows
    ]

    return AgentHubConfig(
        routes,
        source="database",
        mcp_tool_permissions=permissions,
        risk_rules=risk_rules,
    ) if routes else None


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


def _fallback_risk_rules() -> list[AgentRiskRule]:
    return [
        AgentRiskRule("command_contains", "rm -rf /", "block", "high", "Blocks recursive root deletion.", 1),
        AgentRiskRule("command_contains", "mkfs", "block", "high", "Blocks filesystem formatting.", 2),
        AgentRiskRule("command_contains", "dd if=", "block", "high", "Blocks raw disk overwrite patterns.", 3),
        AgentRiskRule("command_contains", "shutdown", "block", "high", "Blocks shutdown commands.", 4),
        AgentRiskRule("command_contains", "reboot", "block", "high", "Blocks reboot commands.", 5),
        AgentRiskRule("command_contains", "del /s /q c:\\", "block", "high", "Blocks Windows drive deletion.", 6),
        AgentRiskRule("path_prefix", r"c:\windows", "block", "high", "Blocks Windows system directory mutation.", 10),
        AgentRiskRule("path_prefix", r"c:\program files", "block", "high", "Blocks Program Files mutation.", 11),
        AgentRiskRule("path_prefix", r"c:\programdata", "block", "high", "Blocks ProgramData mutation.", 12),
        AgentRiskRule("path_prefix", "/etc", "block", "high", "Blocks Unix system configuration mutation.", 20),
        AgentRiskRule("path_prefix", "/bin", "block", "high", "Blocks Unix binary directory mutation.", 21),
        AgentRiskRule("path_prefix", "/sbin", "block", "high", "Blocks Unix system binary directory mutation.", 22),
        AgentRiskRule("path_prefix", "/usr/bin", "block", "high", "Blocks Unix binary directory mutation.", 23),
        AgentRiskRule("path_prefix", "/usr/sbin", "block", "high", "Blocks Unix system binary directory mutation.", 24),
        AgentRiskRule("path_prefix", "/root", "block", "high", "Blocks root home mutation.", 25),
        AgentRiskRule("path_prefix", "/var/lib", "block", "high", "Blocks service state mutation.", 26),
        AgentRiskRule("path_prefix", "/boot", "block", "high", "Blocks boot directory mutation.", 27),
        AgentRiskRule("path_prefix", "/sys", "block", "high", "Blocks kernel/system mutation.", 28),
        AgentRiskRule("path_prefix", "/dev", "block", "high", "Blocks device mutation.", 29),
        AgentRiskRule("intent_key", "FILE_SYSTEM_WRITE", "require_approval", "medium", "File writes require user approval.", 40),
        AgentRiskRule("intent_key", "APP_CONTROL", "require_approval", "medium", "Application control requires user approval.", 41),
        AgentRiskRule("intent_key", "DEVOPS_WRITE", "require_approval", "medium", "DevOps write operations require user approval.", 42),
        AgentRiskRule("intent_key", "SYSTEM_OPERATION", "require_approval", "medium", "System operations require user approval unless routed to read-only MCP.", 43),
        AgentRiskRule("intent_key", "UNKNOWN", "require_approval", "high", "Unknown actions require user approval.", 44),
    ]
