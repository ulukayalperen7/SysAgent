import unittest

from agents.langgraph.nodes.chat import direct_chat_node
from agents.langgraph.nodes.intent import _detect_intent_deterministic
from agents.langgraph.nodes.planner import _deterministic_decompose
from core.response_parse import parse_explanation_and_script
from core.script_policy import propose_deterministic_script, validate_command_risk


class TerminalHardeningTests(unittest.TestCase):
    def test_decompose_mixed_queue_steps(self):
        tasks = _deterministic_decompose(
            "open Spotify sonra next song sonra create test.txt on desktop"
        )

        self.assertEqual(tasks, ["open Spotify", "next song", "create test.txt on desktop"])

    def test_chat_shortcut_does_not_need_llm(self):
        result = direct_chat_node(
            {
                "user_input": "hello",
                "messages": [],
                "explanation": "",
                "script": "NONE",
            }
        )

        self.assertEqual(result["script"], "NONE")
        self.assertIn("SysAgent is ready", result["explanation"])

    def test_deterministic_intent_detects_app_and_file_write(self):
        self.assertEqual(_detect_intent_deterministic("open Spotify"), "APP_CONTROL")
        self.assertEqual(_detect_intent_deterministic("delete test.txt from desktop"), "FILE_SYSTEM_WRITE")

    def test_windows_open_app_proposal_is_review_only(self):
        proposal = propose_deterministic_script("open Spotify", "APP_CONTROL", "Windows")

        self.assertIsNotNone(proposal)
        self.assertIn("Start-Process", proposal.script)
        self.assertEqual(proposal.risk_level, "Medium")

    def test_windows_media_next_proposal_uses_virtual_key(self):
        proposal = propose_deterministic_script("next song", "APP_CONTROL", "Windows")

        self.assertIsNotNone(proposal)
        self.assertIn("0xB0", proposal.script)

    def test_file_delete_is_high_risk(self):
        proposal = propose_deterministic_script("delete test.txt from desktop", "FILE_SYSTEM_WRITE", "Windows")

        self.assertIsNotNone(proposal)
        risk = validate_command_risk(proposal.script, "FILE_SYSTEM_WRITE", "Windows")
        self.assertEqual(risk.risk_level, "High")

    def test_parser_strips_fences_and_extra_sections(self):
        explanation, script = parse_explanation_and_script(
            "Explanation: do thing\nScript: ```powershell\nGet-Process\n```\nRollback: none"
        )

        self.assertEqual(explanation, "do thing")
        self.assertEqual(script, "Get-Process")


if __name__ == "__main__":
    unittest.main()
