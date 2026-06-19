import unittest
from unittest.mock import patch

from agents.langgraph.nodes.mcp_read import is_mcp_read_only_supported, mcp_read_only_node


def _state(user_input: str, intent: str) -> dict:
    return {
        "thread_id": "test-thread",
        "user_input": user_input,
        "messages": [{"role": "user", "content": user_input}],
        "metrics": {},
        "os_type": "Windows",
        "current_intent": intent,
        "task_queue": [],
        "explanation": "",
        "script": "NONE",
        "errors": [],
        "retry_count": 0,
    }


class LangGraphMcpReadTests(unittest.TestCase):
    def test_top_memory_system_operation_uses_mcp(self):
        state = _state("show top 3 memory processes", "SYSTEM_OPERATION")

        self.assertTrue(is_mcp_read_only_supported(state))

        result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertIn("Top memory-consuming processes", result["explanation"])
        self.assertEqual(result["mcp_tools_used"], ["system_get_top_memory_processes"])

    def test_directory_listing_uses_mcp(self):
        state = _state("list files in this project", "FILE_SYSTEM_READ")

        self.assertTrue(is_mcp_read_only_supported(state))

        result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertTrue("Directory listed successfully" in result["explanation"] or "could not map" in result["explanation"])

    def test_network_read_uses_mcp(self):
        state = _state("show network connections", "NETWORK_READ")

        self.assertTrue(is_mcp_read_only_supported(state))

        result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertIn("network connections", result["explanation"].lower())

    def test_network_interfaces_use_mcp(self):
        state = _state("show network interfaces and IP addresses", "NETWORK_READ")

        self.assertTrue(is_mcp_read_only_supported(state))

        result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertIn("Network interfaces inspected", result["explanation"])
        self.assertEqual(result["mcp_tools_used"], ["network_list_interfaces"])

    def test_disk_partitions_use_mcp(self):
        state = _state("show disk partitions and drives", "SYSTEM_OPERATION")

        self.assertTrue(is_mcp_read_only_supported(state))

        result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertIn("Disk partitions inspected", result["explanation"])
        self.assertEqual(result["mcp_tools_used"], ["system_get_disk_partitions"])

    def test_filesystem_search_uses_mcp(self):
        state = _state("find file requirements.txt in this project", "FILE_SYSTEM_READ")

        self.assertTrue(is_mcp_read_only_supported(state))

        result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertIn("Filesystem search completed", result["explanation"])
        self.assertEqual(result["mcp_tools_used"], ["filesystem_search"])

    def test_git_status_uses_mcp(self):
        state = _state("git status in this project", "DEVOPS_READ")

        self.assertTrue(is_mcp_read_only_supported(state))

        result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertIn("Git status inspected", result["explanation"])
        self.assertEqual(result["mcp_tools_used"], ["devops_git_status"])

    def test_npm_scripts_use_mcp(self):
        state = _state("show npm scripts in ../frontend", "DEVOPS_READ")

        self.assertTrue(is_mcp_read_only_supported(state))

        result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertIn("package.json scripts", result["explanation"])
        self.assertEqual(result["mcp_tools_used"], ["devops_list_npm_scripts"])

    def test_disk_usage_uses_mcp(self):
        state = _state("show disk usage of this project", "FILE_SYSTEM_READ")

        self.assertTrue(is_mcp_read_only_supported(state))

        result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertIn("Disk usage scan completed", result["explanation"])

    def test_deep_diagnostic_system_operation_stays_with_crewai(self):
        state = _state("my laptop is slow, investigate why", "SYSTEM_OPERATION")

        self.assertFalse(is_mcp_read_only_supported(state))

    def test_risky_file_write_does_not_use_mcp(self):
        state = _state("delete all temp files", "FILE_SYSTEM_WRITE")

        self.assertFalse(is_mcp_read_only_supported(state))

    def test_agent_hub_permission_can_disable_selected_mcp_tool(self):
        class DenyAllConfig:
            def is_mcp_tool_allowed(self, agent_slug: str, tool_name: str) -> bool:
                return False

        state = _state("show top 3 memory processes", "SYSTEM_OPERATION")

        with patch("agents.langgraph.nodes.mcp_read.get_agent_hub_config", return_value=DenyAllConfig()):
            result = mcp_read_only_node(state)

        self.assertEqual(result["script"], "NONE")
        self.assertIn("not enabled", result["explanation"])


if __name__ == "__main__":
    unittest.main()
