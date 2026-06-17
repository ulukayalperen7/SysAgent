import unittest

from core.agent_hub import (
    AgentHubConfig,
    AgentRiskRule,
    AgentRoute,
    get_agent_hub_config,
    reload_agent_hub_config,
)


class AgentHubConfigTests(unittest.TestCase):
    def test_fallback_routes_read_only_intent_to_mcp_node(self):
        config = reload_agent_hub_config()

        route = config.select_route("FILE_SYSTEM_READ", "list files in this project")

        self.assertIsNotNone(route)
        self.assertEqual(route.target_langgraph_node, "mcp_read_only_node")

    def test_fallback_routes_diagnostic_system_operation_to_crewai(self):
        config = get_agent_hub_config()

        route = config.select_route("SYSTEM_OPERATION", "my laptop is slow, investigate why")

        self.assertIsNotNone(route)
        self.assertEqual(route.target_langgraph_node, "run_crewai_diagnostics_node")

    def test_fallback_does_not_force_simple_system_metrics_to_crewai(self):
        config = get_agent_hub_config()

        route = config.select_route("SYSTEM_OPERATION", "show top memory processes")

        self.assertIsNone(route)

    def test_route_matcher_uses_diagnostic_terms(self):
        route = AgentRoute(
            intent_key="SYSTEM_OPERATION",
            priority=10,
            route_type="crewai_diagnostics",
            target_langgraph_node="run_crewai_diagnostics_node",
            approval_policy="risk_based",
            matcher={"diagnostic_terms": ["investigate"]},
        )
        config = AgentHubConfig([route], source="test")

        self.assertIsNotNone(config.select_route("SYSTEM_OPERATION", "please investigate cpu"))
        self.assertIsNone(config.select_route("SYSTEM_OPERATION", "show cpu usage"))

    def test_status_payload_exposes_safe_route_summary(self):
        config = get_agent_hub_config()

        payload = config.to_dict()

        self.assertIn(payload["source"], {"fallback", "database"})
        self.assertGreater(payload["route_count"], 0)
        self.assertIn("intent_key", payload["routes"][0])
        self.assertIn("target_langgraph_node", payload["routes"][0])
        self.assertIn("mcp_read_agent", payload["mcp_tool_permissions"])
        self.assertIn("filesystem_read_file", payload["mcp_tool_permissions"]["mcp_read_agent"])

    def test_fallback_mcp_permissions_allow_seeded_read_tools(self):
        config = get_agent_hub_config()

        self.assertTrue(config.is_mcp_tool_allowed("mcp_read_agent", "system_get_metrics_snapshot"))
        self.assertFalse(config.is_mcp_tool_allowed("mcp_read_agent", "unsafe_shell_exec"))

    def test_fallback_risk_rules_block_dangerous_commands(self):
        config = get_agent_hub_config()

        reason = config.command_block_reason("rm -rf /", "Linux")

        self.assertIsNotNone(reason)
        self.assertIn("root deletion", reason)

    def test_risk_rules_can_require_approval_for_intent(self):
        config = AgentHubConfig(
            routes=[],
            source="test",
            risk_rules=[
                AgentRiskRule(
                    rule_type="intent_key",
                    pattern="DEVOPS_WRITE",
                    effect="require_approval",
                    risk_level="medium",
                    reason="DevOps writes require approval.",
                    priority=1,
                )
            ],
        )

        self.assertTrue(config.requires_approval("DEVOPS_WRITE"))
        self.assertIsNone(config.requires_approval("CHAT"))


if __name__ == "__main__":
    unittest.main()
