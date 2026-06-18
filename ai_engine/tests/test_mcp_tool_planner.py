import unittest

from core.mcp_tool_planner import plan_mcp_read_tool


class McpToolPlannerTests(unittest.TestCase):
    def test_plans_filesystem_search_before_file_read(self):
        plan = plan_mcp_read_tool("find file requirements.txt in this project", "FILE_SYSTEM_READ")

        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool_name, "filesystem_search")
        self.assertEqual(plan.arguments["pattern"], "requirements.txt")

    def test_plans_disk_usage(self):
        plan = plan_mcp_read_tool("show disk usage of this project", "FILE_SYSTEM_READ")

        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool_name, "filesystem_get_disk_usage")

    def test_plans_top_memory_processes(self):
        plan = plan_mcp_read_tool("show top 3 memory processes", "SYSTEM_OPERATION")

        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool_name, "system_get_top_memory_processes")
        self.assertEqual(plan.arguments["limit"], 3)

    def test_plans_network_interfaces(self):
        plan = plan_mcp_read_tool("show network interfaces and IP addresses", "NETWORK_READ")

        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool_name, "network_list_interfaces")

    def test_plans_disk_partitions(self):
        plan = plan_mcp_read_tool("show disk partitions and drives", "SYSTEM_OPERATION")

        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool_name, "system_get_disk_partitions")

    def test_plans_installed_apps(self):
        plan = plan_mcp_read_tool("show installed apps matching code", "SYSTEM_OPERATION")

        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool_name, "system_list_installed_apps")
        self.assertEqual(plan.arguments["query"], "code")

    def test_does_not_plan_for_write_intents(self):
        plan = plan_mcp_read_tool("delete temp files", "FILE_SYSTEM_WRITE")

        self.assertIsNone(plan)

    def test_turkish_search_terms_are_supported(self):
        plan = plan_mcp_read_tool("bu projede requirements.txt dosya bul", "FILE_SYSTEM_READ")

        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool_name, "filesystem_search")


if __name__ == "__main__":
    unittest.main()
