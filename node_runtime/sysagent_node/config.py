from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def config_path() -> Path:
    override = os.environ.get("SYSAGENT_NODE_CONFIG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".sysagent-node" / "config.json"


@dataclass(frozen=True)
class NodeConfig:
    server_url: str
    device_id: int
    node_token: str
    heartbeat_interval_seconds: int = 30

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "NodeConfig":
        return NodeConfig(
            server_url=str(data["server_url"]).rstrip("/"),
            device_id=int(data["device_id"]),
            node_token=str(data["node_token"]),
            heartbeat_interval_seconds=int(data.get("heartbeat_interval_seconds") or 30),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_url": self.server_url.rstrip("/"),
            "device_id": self.device_id,
            "node_token": self.node_token,
            "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
        }


def load_config(path: Path | None = None) -> NodeConfig:
    target = path or config_path()
    if not target.exists():
        raise FileNotFoundError(f"Node is not registered yet. Missing config: {target}")
    return NodeConfig.from_dict(json.loads(target.read_text(encoding="utf-8")))


def save_config(config: NodeConfig, path: Path | None = None) -> Path:
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    return target
