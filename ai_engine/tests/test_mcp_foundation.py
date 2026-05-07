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
        self.assertIn("filesystem_list_directory", tools)
        self.assertIn("filesystem_read_file", tools)
        self.assertIn("system_get_platform_info", tools)

    def test_platform_info_is_available(self):
        result = local_system_mcp_client.call_tool("system_get_platform_info")

        self.assertTrue(result["success"])
        self.assertIn("system", result["data"])

    def test_process_listing_is_bounded(self):
        result = local_system_mcp_client.call_tool("system_get_top_memory_processes", {"limit": 3})

        self.assertTrue(result["success"])
        self.assertLessEqual(result["data"]["count"], 3)

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


if __name__ == "__main__":
    unittest.main()
