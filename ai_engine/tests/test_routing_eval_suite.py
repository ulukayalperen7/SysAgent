import json
import unittest
from pathlib import Path

from agents.langgraph.nodes.intent import _detect_intent_deterministic
from core.mcp_tool_planner import plan_mcp_read_tool
from core.security_guardian import SecurityGuardian


class RoutingEvalSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases_path = Path(__file__).parent / "evals" / "read_only_routing_cases.json"
        cls.cases = json.loads(cases_path.read_text(encoding="utf-8"))

    def test_eval_cases_have_expected_intent_tool_and_approval(self):
        failures = []
        for case in self.cases:
            prompt = case["prompt"]
            expected_intent = case["expected_intent"]
            intent = _detect_intent_deterministic(prompt)
            if intent != expected_intent:
                failures.append(f"{case['name']}: intent {intent!r} != {expected_intent!r}")
                continue

            plan = plan_mcp_read_tool(prompt, intent)
            expected_tool = case["expected_tool"]
            actual_tool = plan.tool_name if plan else None
            if actual_tool != expected_tool:
                failures.append(f"{case['name']}: tool {actual_tool!r} != {expected_tool!r}")

            approval_required = False if expected_tool else SecurityGuardian.requires_approval(intent)
            if approval_required != case["approval_required"]:
                failures.append(
                    f"{case['name']}: approval {approval_required!r} != {case['approval_required']!r}"
                )

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
