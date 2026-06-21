import unittest
from pathlib import Path
from unittest.mock import patch

from sysagent_node.config import NodeConfig
from sysagent_node.diagnostics import run_diagnostics


class DiagnosticsTests(unittest.TestCase):
    def test_reports_missing_config(self):
        checks = run_diagnostics(None, Path("/tmp/missing.json"), "WINDOWS", check_backend=False)

        self.assertFalse(checks[0].ok)
        self.assertEqual(checks[0].name, "config")

    def test_checks_backend_with_node_token(self):
        cfg = NodeConfig(server_url="http://localhost:8080", device_id=42, node_token="token")
        with patch("sysagent_node.diagnostics.SysAgentApi") as api:
            api.return_value.next_command.return_value = None
            checks = run_diagnostics(cfg, Path("/tmp/config.json"), "WINDOWS", check_backend=True)

        backend = next(check for check in checks if check.name == "backend-auth")
        self.assertTrue(backend.ok)
        api.return_value.next_command.assert_called_once_with(42)


if __name__ == "__main__":
    unittest.main()
