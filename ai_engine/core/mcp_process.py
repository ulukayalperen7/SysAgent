"""Lifecycle helpers for the local SysAgent MCP server process."""

from __future__ import annotations

import importlib.util
import socket
import subprocess
import sys
import time
from pathlib import Path

from core.config import settings

_mcp_process: subprocess.Popen | None = None


def ensure_local_mcp_server() -> bool:
    """Start the local MCP server when configured, returning whether a port is reachable."""
    global _mcp_process

    if not settings.mcp_auto_start or settings.mcp_transport != "streamable-http":
        return _is_port_open()

    if _is_port_open():
        return True

    if importlib.util.find_spec("mcp") is None:
        return False

    if _mcp_process is not None and _mcp_process.poll() is None:
        return _wait_for_port()

    ai_engine_root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "-m",
        "mcp_servers.local_system_server",
        "--transport",
        settings.mcp_transport,
        "--host",
        settings.mcp_host,
        "--port",
        str(settings.mcp_port),
    ]
    _mcp_process = subprocess.Popen(
        command,
        cwd=str(ai_engine_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_creation_flags(),
    )
    return _wait_for_port()


def _wait_for_port() -> bool:
    deadline = time.monotonic() + settings.mcp_connect_timeout_seconds
    while time.monotonic() < deadline:
        if _is_port_open():
            return True
        time.sleep(0.1)
    return False


def _is_port_open() -> bool:
    try:
        with socket.create_connection((settings.mcp_host, settings.mcp_port), timeout=0.25):
            return True
    except OSError:
        return False


def _creation_flags() -> int:
    if sys.platform != "win32":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)
