import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from sysagent_node.cli import _doctor, _poll_once, main
from sysagent_node.config import NodeConfig
from sysagent_node.diagnostics import DiagnosticCheck


class FakeApi:
    instances = []

    def __init__(self, server_url, node_token=None):
        self.server_url = server_url
        self.node_token = node_token
        self.command_result_payload = None
        FakeApi.instances.append(self)

    def register(self, token, name, ip_address, node_type):
        return {
            "data": {
                "device": {"id": 42},
                "nodeToken": "node-token",
                "heartbeatIntervalSeconds": 30,
            }
        }

    def next_command(self, device_id):
        return {
            "id": "command-1",
            "taskId": "task-1",
            "script": "echo ok",
        }

    def command_result(self, command_id, payload):
        self.command_result_payload = (command_id, payload)


class EmptyApi(FakeApi):
    def next_command(self, device_id):
        return None


class CliPollingTests(unittest.TestCase):
    def setUp(self):
        FakeApi.instances = []
        self.cfg = NodeConfig(
            server_url="http://localhost:8080",
            device_id=42,
            node_token="node-token",
        )

    def test_remote_flow_executes_reports_result_and_submits_fresh_context(self):
        with patch("sysagent_node.cli.SysAgentApi", FakeApi), \
             patch("sysagent_node.cli.execute_script", return_value={"success": True, "output": "ok", "error": None}), \
             patch("sysagent_node.cli._submit_context") as submit_context, \
             patch("sys.stdout", new_callable=StringIO):
            exit_code = _poll_once(self.cfg)

        self.assertEqual(exit_code, 0)
        self.assertEqual(FakeApi.instances[0].command_result_payload[0], "command-1")
        self.assertEqual(FakeApi.instances[0].command_result_payload[1]["deviceId"], 42)
        self.assertTrue(FakeApi.instances[0].command_result_payload[1]["success"])
        self.assertEqual(FakeApi.instances[0].command_result_payload[1]["output"], "ok")
        submit_context.assert_called_once()
        args, kwargs = submit_context.call_args
        self.assertEqual(args[0], self.cfg)
        self.assertEqual(kwargs["extra_metadata"]["post_command"], True)
        self.assertEqual(kwargs["extra_metadata"]["command_id"], "command-1")
        self.assertEqual(kwargs["extra_metadata"]["task_id"], "task-1")
        self.assertEqual(kwargs["extra_metadata"]["command_success"], True)

    def test_poll_once_does_not_submit_context_when_no_command_exists(self):
        with patch("sysagent_node.cli.SysAgentApi", EmptyApi), \
             patch("sysagent_node.cli._submit_context") as submit_context, \
             patch("sys.stdout", new_callable=StringIO):
            exit_code = _poll_once(self.cfg)

        self.assertEqual(exit_code, 0)
        submit_context.assert_not_called()

    def test_doctor_reports_missing_config(self):
        with TemporaryDirectory() as temp:
            missing = Path(temp) / "missing.json"
            with patch("sys.stdout", new_callable=StringIO) as output:
                exit_code = _doctor(missing, check_backend=False)

        self.assertEqual(exit_code, 2)
        self.assertIn("[FAIL] config", output.getvalue())

    def test_service_install_requires_registered_config(self):
        with TemporaryDirectory() as temp:
            missing = Path(temp) / "missing.json"
            with patch("sys.stderr", new_callable=StringIO) as error_output:
                exit_code = main(["service-install", "--config", str(missing)])

        self.assertEqual(exit_code, 1)
        self.assertIn("Node is not registered yet", error_output.getvalue())

    def test_bootstrap_registers_runs_diagnostics_and_prepares_service_plan(self):
        class Plan:
            path = Path("service-file")
            commands = ["enable service"]

        with TemporaryDirectory() as temp:
            config = Path(temp) / "config.json"
            with patch("sysagent_node.cli.SysAgentApi", FakeApi), \
                 patch(
                     "sysagent_node.cli.run_diagnostics",
                     return_value=[
                         DiagnosticCheck("config", True, "ok"),
                         DiagnosticCheck("backend-auth", True, "ok"),
                     ],
                 ) as diagnostics, \
                 patch("sysagent_node.cli.create_install_plan", return_value=Plan()) as install_plan, \
                 patch("sys.stdout", new_callable=StringIO) as output:
                exit_code = main([
                    "bootstrap",
                    "--server", "http://localhost:8080",
                    "--token", "registration-token",
                    "--config", str(config),
                    "--type", "WINDOWS",
                    "--install-service",
                ])

        self.assertEqual(exit_code, 0)
        self.assertIn("Registered device 42", output.getvalue())
        self.assertIn("Service plan is ready", output.getvalue())
        diagnostics.assert_called_once()
        install_plan.assert_called_once()


if __name__ == "__main__":
    unittest.main()
