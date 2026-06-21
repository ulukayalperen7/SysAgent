from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from sysagent_node.config import NodeConfig
from sysagent_node.http_client import ApiError, SysAgentApi


@dataclass(frozen=True)
class DiagnosticCheck:
    name: str
    ok: bool
    detail: str


def run_diagnostics(
    cfg: NodeConfig | None,
    cfg_path: Path,
    node_type: str,
    check_backend: bool = True,
) -> list[DiagnosticCheck]:
    checks: list[DiagnosticCheck] = [
        DiagnosticCheck(
            "config",
            cfg is not None,
            f"Found config at {cfg_path}." if cfg else f"Missing config at {cfg_path}. Run sysagent-node register first.",
        )
    ]

    if cfg is not None:
        checks.append(DiagnosticCheck("server-url", bool(cfg.server_url), cfg.server_url or "Missing server URL."))
        checks.append(DiagnosticCheck("device-id", cfg.device_id > 0, str(cfg.device_id)))
        checks.append(DiagnosticCheck("node-token", bool(cfg.node_token), "Configured." if cfg.node_token else "Missing node token."))
        if check_backend:
            checks.append(_backend_check(cfg))

    checks.extend(_gui_helper_checks(node_type))
    return checks


def _backend_check(cfg: NodeConfig) -> DiagnosticCheck:
    try:
        SysAgentApi(cfg.server_url, cfg.node_token, timeout=8).next_command(cfg.device_id)
        return DiagnosticCheck("backend-auth", True, "Backend accepted node token.")
    except ApiError as exc:
        return DiagnosticCheck("backend-auth", False, str(exc))


def _gui_helper_checks(node_type: str) -> list[DiagnosticCheck]:
    normalized = (node_type or "").upper()
    if normalized == "LINUX":
        return [
            DiagnosticCheck(
                "gui-helper-xdotool",
                shutil.which("xdotool") is not None,
                "xdotool found." if shutil.which("xdotool") else "xdotool missing; GUI click/type helpers will fail.",
            )
        ]
    if normalized == "MACOS":
        return [
            DiagnosticCheck(
                "gui-helper-cliclick",
                shutil.which("cliclick") is not None,
                "cliclick found." if shutil.which("cliclick") else "cliclick missing; coordinate click helpers will fail.",
            )
        ]
    if normalized == "WINDOWS":
        return [DiagnosticCheck("gui-helper-win32", True, "Built-in PowerShell/Win32 helpers are available.")]
    return [DiagnosticCheck("gui-helper", False, f"Unknown node type: {node_type}")]
