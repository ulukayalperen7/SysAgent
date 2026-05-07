import unittest

from agents.crewai.mcp_tool_wrappers import build_network_audit_report, build_system_audit_report


class CrewAiMcpWrapperTests(unittest.TestCase):
    def test_system_audit_report_uses_expected_contract(self):
        report = build_system_audit_report()

        self.assertIn("TOP 10 PROCESSES BY RAM USAGE:", report)
        self.assertTrue("PID:" in report or "No process data available" in report)

    def test_system_audit_report_supports_query_matches(self):
        report = build_system_audit_report("definitely-not-a-real-process-name-for-test")

        self.assertIn("TOP 10 PROCESSES BY RAM USAGE:", report)
        self.assertIn("NO PROCESSES FOUND MATCHING", report)

    def test_network_audit_report_uses_expected_contract(self):
        report = build_network_audit_report()

        self.assertTrue(
            report.startswith("ACTIVE NETWORK CONNECTIONS")
            or report == "No active ESTABLISHED connections found at this moment."
            or report.startswith("Network audit failed:")
        )


if __name__ == "__main__":
    unittest.main()
