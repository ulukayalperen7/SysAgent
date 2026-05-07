import unittest

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

    def test_deep_diagnostic_system_operation_stays_with_crewai(self):
        state = _state("my laptop is slow, investigate why", "SYSTEM_OPERATION")

        self.assertFalse(is_mcp_read_only_supported(state))

    def test_risky_file_write_does_not_use_mcp(self):
        state = _state("delete all temp files", "FILE_SYSTEM_WRITE")

        self.assertFalse(is_mcp_read_only_supported(state))


if __name__ == "__main__":
    unittest.main()
