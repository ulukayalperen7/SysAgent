import unittest

from sysagent_node.executor import execute_script, validate_script


class ExecutorPolicyTests(unittest.TestCase):

    def test_blocks_dangerous_patterns(self):
        self.assertIn("Blocked", validate_script("rm -rf /"))
        result = execute_script("shutdown now")
        self.assertFalse(result["success"])
        self.assertIn("Blocked", result["error"])

    def test_allows_simple_echo(self):
        result = execute_script("echo sysagent-node-ok")
        self.assertTrue(result["success"])
        self.assertIn("sysagent-node-ok", result["output"])


if __name__ == "__main__":
    unittest.main()
