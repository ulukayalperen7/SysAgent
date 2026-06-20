from __future__ import annotations

import argparse
import socket
import sys
import time
from pathlib import Path

from sysagent_node import __version__
from sysagent_node.config import NodeConfig, config_path, load_config, save_config
from sysagent_node.desktop_context import collect_desktop_context
from sysagent_node.executor import execute_script
from sysagent_node.http_client import ApiError, SysAgentApi
from sysagent_node.metrics import collect_metrics
from sysagent_node.service import create_install_plan, create_uninstall_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sysagent-node")
    subcommands = parser.add_subparsers(dest="command", required=True)

    register = subcommands.add_parser("register")
    register.add_argument("--server", required=True)
    register.add_argument("--token", required=True)
    register.add_argument("--name", default=socket.gethostname())
    register.add_argument("--type", choices=["WINDOWS", "LINUX", "MACOS"], default=_default_type())
    register.add_argument("--config", type=Path)

    status = subcommands.add_parser("status")
    status.add_argument("--config", type=Path)

    heartbeat = subcommands.add_parser("heartbeat")
    heartbeat.add_argument("--config", type=Path)

    context = subcommands.add_parser("context")
    context.add_argument("--config", type=Path)
    context.add_argument("--no-screenshot", action="store_true")
    context.add_argument("--max-width", type=int, default=1280)

    poll = subcommands.add_parser("poll-once")
    poll.add_argument("--config", type=Path)

    run = subcommands.add_parser("run")
    run.add_argument("--config", type=Path)
    run.add_argument("--poll-interval", type=int, default=3)
    run.add_argument("--context-interval", type=int, default=120)

    service_install = subcommands.add_parser("service-install")
    service_install.add_argument("--config", type=Path)
    service_install.add_argument("--poll-interval", type=int, default=3)
    service_install.add_argument("--context-interval", type=int, default=120)
    service_install.add_argument("--apply", action="store_true")

    service_uninstall = subcommands.add_parser("service-uninstall")
    service_uninstall.add_argument("--apply", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "register":
            return _register(args)
        if args.command == "status":
            return _status(args.config)
        if args.command == "heartbeat":
            cfg = load_config(args.config)
            _heartbeat(cfg)
            print("Heartbeat accepted.")
            return 0
        if args.command == "context":
            cfg = load_config(args.config)
            _submit_context(cfg, include_screenshot=not args.no_screenshot, max_width=args.max_width)
            print("Desktop context accepted.")
            return 0
        if args.command == "poll-once":
            cfg = load_config(args.config)
            return _poll_once(cfg)
        if args.command == "run":
            cfg = load_config(args.config)
            return _run(cfg, args.poll_interval, args.context_interval)
        if args.command == "service-install":
            return _service_install(args.config, args.poll_interval, args.context_interval, args.apply)
        if args.command == "service-uninstall":
            return _service_uninstall(args.apply)
    except (ApiError, FileNotFoundError, KeyError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 1


def _register(args: argparse.Namespace) -> int:
    api = SysAgentApi(args.server)
    response = api.register(args.token, args.name, None, args.type)
    data = response.get("data") or {}
    device = data.get("device") or {}
    cfg = NodeConfig(
        server_url=args.server,
        device_id=int(device["id"]),
        node_token=str(data["nodeToken"]),
        heartbeat_interval_seconds=int(data.get("heartbeatIntervalSeconds") or 30),
    )
    saved = save_config(cfg, args.config)
    print(f"Registered device {cfg.device_id}. Config saved to {saved}.")
    return 0


def _status(path: Path | None = None) -> int:
    target = path or config_path()
    if not target.exists():
        print(f"Not registered. Missing config: {target}")
        return 1
    cfg = load_config(target)
    print(f"Registered device {cfg.device_id} -> {cfg.server_url}")
    return 0


def _heartbeat(cfg: NodeConfig) -> None:
    api = SysAgentApi(cfg.server_url, cfg.node_token)
    payload = {
        "deviceId": cfg.device_id,
        "nodeVersion": __version__,
        "hostname": socket.gethostname(),
        "type": _default_type(),
    }
    payload.update(collect_metrics())
    api.heartbeat(payload)


def _submit_context(cfg: NodeConfig, include_screenshot: bool = True, max_width: int = 1280) -> None:
    api = SysAgentApi(cfg.server_url, cfg.node_token)
    payload = collect_desktop_context(include_screenshot=include_screenshot, max_width=max_width)
    payload["deviceId"] = cfg.device_id
    api.submit_context(payload)


def _poll_once(cfg: NodeConfig) -> int:
    api = SysAgentApi(cfg.server_url, cfg.node_token)
    command = api.next_command(cfg.device_id)
    if not command:
        print("No command.")
        return 0

    command_id = str(command["id"])
    script = str(command["script"])
    print(f"Executing command {command_id} for task {command.get('taskId')}.")
    result = execute_script(script)
    api.command_result(command_id, {
        "deviceId": cfg.device_id,
        "success": bool(result["success"]),
        "output": result.get("output"),
        "error": result.get("error"),
    })
    print("Result submitted.")
    return 0 if result["success"] else 2


def _run(cfg: NodeConfig, poll_interval: int, context_interval: int) -> int:
    next_heartbeat = 0.0
    next_context = 0.0
    print(f"SysAgent node running for device {cfg.device_id}. Press Ctrl+C to stop.")
    try:
        while True:
            now = time.monotonic()
            if now >= next_heartbeat:
                _heartbeat(cfg)
                next_heartbeat = now + cfg.heartbeat_interval_seconds
            if context_interval > 0 and now >= next_context:
                try:
                    _submit_context(cfg)
                except (ApiError, OSError, ValueError) as exc:
                    print(f"Desktop context warning: {exc}", file=sys.stderr)
                next_context = now + max(30, context_interval)
            _poll_once(cfg)
            time.sleep(max(1, poll_interval))
    except KeyboardInterrupt:
        print("Stopped.")
        return 0


def _service_install(path: Path | None, poll_interval: int, context_interval: int, apply: bool) -> int:
    plan = create_install_plan(path, poll_interval, context_interval, apply=apply)
    print(f"Service file written to {plan.path}.")
    for command in plan.commands:
        print(f"Run: {command}")
    if apply:
        print("Service installation command completed.")
    else:
        print("Re-run with --apply to execute these commands.")
    return 0


def _service_uninstall(apply: bool) -> int:
    plan = create_uninstall_plan(apply=apply)
    print(f"Service uninstall plan for {plan.path}.")
    for command in plan.commands:
        print(f"Run: {command}")
    if apply:
        print("Service uninstall command completed.")
    else:
        print("Re-run with --apply to execute these commands.")
    return 0


def _default_type() -> str:
    value = sys.platform.lower()
    if value.startswith("win"):
        return "WINDOWS"
    if value == "darwin":
        return "MACOS"
    return "LINUX"


if __name__ == "__main__":
    raise SystemExit(main())
