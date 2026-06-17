import unittest

from core.security_guardian import SecurityGuardian


class SecurityGuardianPolicyTests(unittest.TestCase):
    def test_agent_hub_policy_blocks_dangerous_command(self):
        allowed, reason = SecurityGuardian.validate_command("shutdown /s", "Windows")

        self.assertFalse(allowed)
        self.assertIn("Security policy blocked", reason)

    def test_read_intents_stay_autonomous(self):
        self.assertFalse(SecurityGuardian.requires_approval("FILE_SYSTEM_READ"))
        self.assertFalse(SecurityGuardian.requires_approval("NETWORK_READ"))

    def test_write_intents_require_approval(self):
        self.assertTrue(SecurityGuardian.requires_approval("FILE_SYSTEM_WRITE"))
        self.assertTrue(SecurityGuardian.requires_approval("DEVOPS_WRITE"))


if __name__ == "__main__":
    unittest.main()
