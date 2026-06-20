from __future__ import annotations

import os
import platform
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from sysagent_node.config import config_path

WINDOWS_TASK_NAME = "SysAgentNode"
MACOS_LABEL = "com.sysagent.node"


@dataclass(frozen=True)
class ServicePlan:
    path: Path
    commands: list[str]


def create_install_plan(
    config: Path | None,
    poll_interval: int,
    context_interval: int,
    apply: bool = False,
) -> ServicePlan:
    cfg = config or config_path()
    system = platform.system().lower()
    if system == "windows":
        plan = _windows_install_plan(cfg, poll_interval, context_interval)
    elif system == "darwin":
        plan = _macos_install_plan(cfg, poll_interval, context_interval)
    else:
        plan = _linux_install_plan(cfg, poll_interval, context_interval)

    if apply:
        _run_commands(plan.commands)
    return plan


def create_uninstall_plan(apply: bool = False) -> ServicePlan:
    system = platform.system().lower()
    if system == "windows":
        plan = _windows_uninstall_plan()
    elif system == "darwin":
        plan = _macos_uninstall_plan()
    else:
        plan = _linux_uninstall_plan()

    if apply:
        _run_commands(plan.commands)
    return plan


def _python_module_command(config: Path, poll_interval: int, context_interval: int) -> str:
    return " ".join([
        shlex.quote(sys.executable),
        "-m",
        "sysagent_node.cli",
        "run",
        "--config",
        shlex.quote(str(config)),
        "--poll-interval",
        str(max(1, poll_interval)),
        "--context-interval",
        str(max(0, context_interval)),
    ])


def _linux_install_plan(config: Path, poll_interval: int, context_interval: int) -> ServicePlan:
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_path = unit_dir / "sysagent-node.service"
    unit_dir.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(systemd_unit(config, poll_interval, context_interval), encoding="utf-8")
    return ServicePlan(
        unit_path,
        [
            "systemctl --user daemon-reload",
            "systemctl --user enable --now sysagent-node.service",
        ],
    )


def _linux_uninstall_plan() -> ServicePlan:
    unit_path = Path.home() / ".config" / "systemd" / "user" / "sysagent-node.service"
    return ServicePlan(
        unit_path,
        [
            "systemctl --user disable --now sysagent-node.service",
            "systemctl --user daemon-reload",
        ],
    )


def _macos_install_plan(config: Path, poll_interval: int, context_interval: int) -> ServicePlan:
    agents_dir = Path.home() / "Library" / "LaunchAgents"
    plist_path = agents_dir / f"{MACOS_LABEL}.plist"
    agents_dir.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(launchd_plist(config, poll_interval, context_interval), encoding="utf-8")
    uid = os.getuid() if hasattr(os, "getuid") else "$(id -u)"
    return ServicePlan(
        plist_path,
        [
            f"launchctl bootstrap gui/{uid} {shlex.quote(str(plist_path))}",
            f"launchctl enable gui/{uid}/{MACOS_LABEL}",
            f"launchctl kickstart -k gui/{uid}/{MACOS_LABEL}",
        ],
    )


def _macos_uninstall_plan() -> ServicePlan:
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{MACOS_LABEL}.plist"
    uid = os.getuid() if hasattr(os, "getuid") else "$(id -u)"
    return ServicePlan(
        plist_path,
        [
            f"launchctl bootout gui/{uid}/{MACOS_LABEL}",
            f"rm -f {shlex.quote(str(plist_path))}",
        ],
    )


def _windows_install_plan(config: Path, poll_interval: int, context_interval: int) -> ServicePlan:
    script_dir = Path(os.getenv("APPDATA") or Path.home() / "AppData" / "Roaming") / "SysAgentNode"
    script_path = script_dir / "install-service.ps1"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path.write_text(windows_install_script(config, poll_interval, context_interval), encoding="utf-8")
    return ServicePlan(
        script_path,
        [
            f'powershell -ExecutionPolicy Bypass -File "{script_path}"',
        ],
    )


def _windows_uninstall_plan() -> ServicePlan:
    script_dir = Path(os.getenv("APPDATA") or Path.home() / "AppData" / "Roaming") / "SysAgentNode"
    script_path = script_dir / "uninstall-service.ps1"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path.write_text(windows_uninstall_script(), encoding="utf-8")
    return ServicePlan(
        script_path,
        [
            f'powershell -ExecutionPolicy Bypass -File "{script_path}"',
        ],
    )


def systemd_unit(config: Path, poll_interval: int, context_interval: int) -> str:
    return f"""[Unit]
Description=SysAgent Node Runtime
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={_python_module_command(config, poll_interval, context_interval)}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
"""


def launchd_plist(config: Path, poll_interval: int, context_interval: int) -> str:
    args = [
        sys.executable,
        "-m",
        "sysagent_node.cli",
        "run",
        "--config",
        str(config),
        "--poll-interval",
        str(max(1, poll_interval)),
        "--context-interval",
        str(max(0, context_interval)),
    ]
    arg_items = "\n".join(f"        <string>{_xml_escape(arg)}</string>" for arg in args)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{MACOS_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
{arg_items}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""


def windows_install_script(config: Path, poll_interval: int, context_interval: int) -> str:
    arguments = (
        f'-m sysagent_node.cli run --config "{config}" '
        f"--poll-interval {max(1, poll_interval)} --context-interval {max(0, context_interval)}"
    )
    return f"""$ErrorActionPreference = "Stop"
$taskName = "{WINDOWS_TASK_NAME}"
$action = New-ScheduledTaskAction -Execute "{sys.executable}" -Argument '{arguments}'
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "SysAgent node runtime" -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
"""


def windows_uninstall_script() -> str:
    return f"""$ErrorActionPreference = "Stop"
$taskName = "{WINDOWS_TASK_NAME}"
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {{
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}}
"""


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _run_commands(commands: list[str]) -> None:
    for command in commands:
        subprocess.run(command, shell=True, check=True)
