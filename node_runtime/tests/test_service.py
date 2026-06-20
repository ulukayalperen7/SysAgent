import unittest
from pathlib import Path

from sysagent_node.service import launchd_plist, systemd_unit, windows_install_script, windows_uninstall_script


class ServiceRenderingTest(unittest.TestCase):
    def test_systemd_unit_runs_node_module(self):
        unit = systemd_unit(Path("/tmp/sysagent/config.json"), 4, 90)
        self.assertIn("ExecStart=", unit)
        self.assertIn("-m sysagent_node.cli run", unit)
        self.assertIn("--poll-interval 4", unit)
        self.assertIn("--context-interval 90", unit)

    def test_launchd_plist_has_keepalive(self):
        plist = launchd_plist(Path("/tmp/sysagent/config.json"), 4, 90)
        self.assertIn("<key>KeepAlive</key>", plist)
        self.assertIn("<string>sysagent_node.cli</string>", plist)
        self.assertIn("<string>--context-interval</string>", plist)

    def test_windows_scripts_use_scheduled_task(self):
        install = windows_install_script(Path("C:/sysagent/config.json"), 4, 90)
        uninstall = windows_uninstall_script()
        self.assertIn("Register-ScheduledTask", install)
        self.assertIn("Start-ScheduledTask", install)
        self.assertIn("--context-interval 90", install)
        self.assertIn("Unregister-ScheduledTask", uninstall)


if __name__ == "__main__":
    unittest.main()
