import unittest

from core.runtime_health import dependency_status, runtime_health_status


class RuntimeHealthTests(unittest.TestCase):
    def test_dependency_status_exposes_required_runtime_modules(self):
        status = dependency_status()

        self.assertIn("fastapi", status)
        self.assertIn("langgraph", status)
        self.assertIn("mcp", status)
        self.assertTrue(status["langgraph"]["required"])
        self.assertIsInstance(status["langgraph"]["available"], bool)
        self.assertEqual(status["langgraph"]["module"], "langgraph")

    def test_runtime_health_summarizes_missing_dependencies(self):
        health = runtime_health_status()

        self.assertIn(health["status"], {"ready", "degraded"})
        self.assertIsInstance(health["required_missing"], list)
        self.assertIsInstance(health["optional_missing"], list)
        self.assertIn("dependencies", health)


if __name__ == "__main__":
    unittest.main()
