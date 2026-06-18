from pathlib import Path
import unittest

from core.mcp_client import local_system_mcp_client


class LocalSystemMcpFoundationTests(unittest.TestCase):
    def test_lists_expected_read_only_tools(self):
        tools = set(local_system_mcp_client.list_tools())

        self.assertIn("system_get_metrics_snapshot", tools)
        self.assertIn("system_list_processes", tools)
        self.assertIn("system_get_top_memory_processes", tools)
        self.assertIn("network_list_connections", tools)
        self.assertIn("network_list_interfaces", tools)
        self.assertIn("system_get_disk_partitions", tools)
        self.assertIn("filesystem_list_directory", tools)
        self.assertIn("filesystem_read_file", tools)
        self.assertIn("filesystem_search", tools)
        self.assertIn("filesystem_get_disk_usage", tools)
        self.assertIn("system_get_platform_info", tools)
        self.assertIn("system_list_installed_apps", tools)

    def test_platform_info_is_available(self):
        result = local_system_mcp_client.call_tool("system_get_platform_info")

        self.assertTrue(result["success"])
        self.assertIn("system", result["data"])

    def test_process_listing_is_bounded(self):
        result = local_system_mcp_client.call_tool("system_get_top_memory_processes", {"limit": 3})

        self.assertTrue(result["success"])
        self.assertLessEqual(result["data"]["count"], 3)

    def test_installed_apps_listing_is_bounded(self):
        result = local_system_mcp_client.call_tool("system_list_installed_apps", {"limit": 5})

        self.assertTrue(result["success"])
        self.assertLessEqual(result["data"]["count"], 5)
        self.assertIn("apps", result["data"])

    def test_filesystem_read_blocks_secret_like_files(self):
        env_path = Path(__file__).resolve().parents[1] / ".env"
        result = local_system_mcp_client.call_tool("filesystem_read_file", {"path": str(env_path)})

        self.assertFalse(result["success"])
        self.assertIn("Secret-like files", result["error"])

    def test_filesystem_read_allows_bounded_project_text_file(self):
        requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
        result = local_system_mcp_client.call_tool(
            "filesystem_read_file",
            {"path": str(requirements_path), "max_bytes": 1024},
        )

        self.assertTrue(result["success"])
        self.assertIn("fastapi", result["data"]["content"])

    def test_filesystem_search_is_bounded(self):
        project_path = Path(__file__).resolve().parents[1]
        result = local_system_mcp_client.call_tool(
            "filesystem_search",
            {"path": str(project_path), "pattern": "requirements.txt", "limit": 5, "max_depth": 2},
        )

        self.assertTrue(result["success"])
        self.assertLessEqual(result["data"]["count"], 5)
        self.assertTrue(any(match["name"] == "requirements.txt" for match in result["data"]["matches"]))

    def test_filesystem_disk_usage_returns_size_summary(self):
        project_path = Path(__file__).resolve().parents[1]
        result = local_system_mcp_client.call_tool(
            "filesystem_get_disk_usage",
            {"path": str(project_path), "max_entries": 100},
        )

        self.assertTrue(result["success"])
        self.assertIn("total_bytes", result["data"])
        self.assertIn("file_count", result["data"])

    def test_network_interfaces_are_available(self):
        result = local_system_mcp_client.call_tool("network_list_interfaces")

        self.assertTrue(result["success"])
        self.assertIn("interfaces", result["data"])

    def test_disk_partitions_are_available(self):
        result = local_system_mcp_client.call_tool("system_get_disk_partitions")

        self.assertTrue(result["success"])
        self.assertIn("partitions", result["data"])


if __name__ == "__main__":
    unittest.main()
