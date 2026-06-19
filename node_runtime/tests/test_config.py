import json
import tempfile
import unittest
from pathlib import Path

from sysagent_node.config import NodeConfig, load_config, save_config


class ConfigTests(unittest.TestCase):

    def test_saves_and_loads_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = NodeConfig(
                server_url="http://localhost:8080/",
                device_id=42,
                node_token="secret-token",
                heartbeat_interval_seconds=15,
            )

            save_config(cfg, path)
            raw = json.loads(path.read_text(encoding="utf-8"))
            loaded = load_config(path)

            self.assertEqual(raw["server_url"], "http://localhost:8080")
            self.assertEqual(loaded.device_id, 42)
            self.assertEqual(loaded.node_token, "secret-token")


if __name__ == "__main__":
    unittest.main()
