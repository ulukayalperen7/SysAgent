"""Read-only local system capabilities for the SysAgent MCP layer."""

from __future__ import annotations

import os
import platform
import socket
from pathlib import Path
from typing import Any

import psutil

MAX_DIRECTORY_ENTRIES = 200
MAX_FILE_READ_BYTES = 200_000
MAX_PROCESS_LIMIT = 100
MAX_NETWORK_LIMIT = 100

SECRET_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "application-secret.properties",
    "id_rsa",
    "id_dsa",
}

SECRET_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
}

WINDOWS_RESTRICTED_ROOTS = (
    r"c:\windows",
    r"c:\program files",
    r"c:\program files (x86)",
    r"c:\programdata",
)

UNIX_RESTRICTED_ROOTS = (
    "/etc",
    "/root",
    "/var/lib",
    "/boot",
    "/sys",
    "/dev",
)

SUSPICIOUS_PORTS = {1337, 4444, 5555, 6666, 6667, 31337, 12345}


def _bounded_int(value: int | None, default: int, maximum: int) -> int:
    if value is None:
        return default
    return max(1, min(int(value), maximum))


def _result(success: bool, data: Any = None, error: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"success": success}
    if success:
        payload["data"] = data
    else:
        payload["error"] = error or "Unknown read-only MCP tool error."
    return payload


def _resolve_user_path(path: str | None) -> Path:
    raw_path = path or str(Path.home())
    expanded = os.path.expandvars(os.path.expanduser(raw_path))
    return Path(expanded).resolve()


def _is_under(path: Path, root: str) -> bool:
    try:
        path_str = str(path).lower()
        root_str = str(Path(root).resolve()).lower()
        return path_str == root_str or path_str.startswith(root_str + os.sep)
    except OSError:
        return False


def _is_restricted_path(path: Path) -> bool:
    roots = WINDOWS_RESTRICTED_ROOTS if os.name == "nt" else UNIX_RESTRICTED_ROOTS
    return any(_is_under(path, root) for root in roots)


def _is_secret_file(path: Path) -> bool:
    name = path.name.lower()
    return name in SECRET_FILE_NAMES or path.suffix.lower() in SECRET_SUFFIXES


def system_get_platform_info() -> dict[str, Any]:
    """Return read-only OS and Python runtime information."""
    return _result(
        True,
        {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
        },
    )


def system_get_metrics_snapshot() -> dict[str, Any]:
    """Return a safe snapshot of local CPU, memory, disk, and boot metrics."""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(Path.home().anchor or Path.home()))
        return _result(
            True,
            {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "cpu_count_physical": psutil.cpu_count(logical=False),
                "memory_total_bytes": memory.total,
                "memory_available_bytes": memory.available,
                "memory_used_bytes": memory.used,
                "memory_percent": memory.percent,
                "disk_total_bytes": disk.total,
                "disk_used_bytes": disk.used,
                "disk_free_bytes": disk.free,
                "disk_percent": disk.percent,
                "boot_time_epoch": psutil.boot_time(),
            },
        )
    except Exception as exc:
        return _result(False, error=f"Failed to collect metrics snapshot: {exc}")


def system_list_processes(query: str | None = None, limit: int = 50) -> dict[str, Any]:
    """List local processes with bounded, non-destructive process metadata."""
    process_limit = _bounded_int(limit, 50, MAX_PROCESS_LIMIT)
    query_text = query.lower().strip() if query else ""
    processes: list[dict[str, Any]] = []

    for proc in psutil.process_iter(["pid", "name", "status", "memory_info", "cpu_percent"]):
        try:
            name = proc.info.get("name") or ""
            if query_text and query_text not in name.lower():
                continue

            memory_info = proc.info.get("memory_info")
            memory_mb = round(memory_info.rss / (1024 * 1024), 2) if memory_info else 0
            processes.append(
                {
                    "pid": proc.info.get("pid"),
                    "name": name,
                    "status": proc.info.get("status"),
                    "memory_mb": memory_mb,
                    "cpu_percent": proc.info.get("cpu_percent") or 0,
                }
            )
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

        if len(processes) >= process_limit:
            break

    return _result(True, {"count": len(processes), "processes": processes})


def system_get_top_memory_processes(limit: int = 10) -> dict[str, Any]:
    """Return top local processes sorted by resident memory usage."""
    process_limit = _bounded_int(limit, 10, MAX_PROCESS_LIMIT)
    processes: list[dict[str, Any]] = []

    for proc in psutil.process_iter(["pid", "name", "status", "memory_info", "cpu_percent"]):
        try:
            memory_info = proc.info.get("memory_info")
            memory_mb = round(memory_info.rss / (1024 * 1024), 2) if memory_info else 0
            processes.append(
                {
                    "pid": proc.info.get("pid"),
                    "name": proc.info.get("name") or "",
                    "status": proc.info.get("status"),
                    "memory_mb": memory_mb,
                    "cpu_percent": proc.info.get("cpu_percent") or 0,
                }
            )
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

    processes.sort(key=lambda item: item["memory_mb"], reverse=True)
    top_processes = processes[:process_limit]
    return _result(True, {"count": len(top_processes), "processes": top_processes})


def network_list_connections(limit: int = 50) -> dict[str, Any]:
    """List active local network connections without mutating network state."""
    connection_limit = _bounded_int(limit, 50, MAX_NETWORK_LIMIT)
    connections: list[dict[str, Any]] = []

    try:
        raw_connections = psutil.net_connections(kind="inet")
    except Exception as exc:
        return _result(False, error=f"Failed to read network connections: {exc}")

    for conn in raw_connections:
        if len(connections) >= connection_limit:
            break

        remote_ip = conn.raddr.ip if conn.raddr else None
        remote_port = conn.raddr.port if conn.raddr else None
        local_ip = conn.laddr.ip if conn.laddr else None
        local_port = conn.laddr.port if conn.laddr else None
        process_name = "Unknown"

        if conn.pid:
            try:
                process_name = psutil.Process(conn.pid).name()
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                process_name = f"PID {conn.pid}"

        suspicious = remote_port in SUSPICIOUS_PORTS if remote_port is not None else False
        connections.append(
            {
                "pid": conn.pid,
                "process": process_name,
                "status": conn.status,
                "local_ip": local_ip,
                "local_port": local_port,
                "remote_ip": remote_ip,
                "remote_port": remote_port,
                "suspicious_port": suspicious,
            }
        )

    return _result(True, {"count": len(connections), "connections": connections})


def filesystem_list_directory(path: str | None = None, limit: int = 100) -> dict[str, Any]:
    """List directory entries without modifying the filesystem."""
    entry_limit = _bounded_int(limit, 100, MAX_DIRECTORY_ENTRIES)

    try:
        target = _resolve_user_path(path)
    except Exception as exc:
        return _result(False, error=f"Invalid path: {exc}")

    if _is_restricted_path(target):
        return _result(False, error=f"Restricted path is not available through read-only MCP: {target}")
    if not target.exists():
        return _result(False, error=f"Directory does not exist: {target}")
    if not target.is_dir():
        return _result(False, error=f"Path is not a directory: {target}")

    entries: list[dict[str, Any]] = []
    try:
        for item in sorted(target.iterdir(), key=lambda entry: entry.name.lower()):
            if len(entries) >= entry_limit:
                break
            try:
                stat = item.stat()
                entries.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size_bytes": stat.st_size if item.is_file() else None,
                        "modified_epoch": stat.st_mtime,
                    }
                )
            except (OSError, PermissionError):
                entries.append({"name": item.name, "path": str(item), "type": "unavailable"})
    except Exception as exc:
        return _result(False, error=f"Failed to list directory: {exc}")

    return _result(True, {"path": str(target), "count": len(entries), "entries": entries})


def filesystem_read_file(path: str, max_bytes: int = MAX_FILE_READ_BYTES) -> dict[str, Any]:
    """Read a bounded text file without modifying the filesystem."""
    read_limit = _bounded_int(max_bytes, MAX_FILE_READ_BYTES, MAX_FILE_READ_BYTES)

    try:
        target = _resolve_user_path(path)
    except Exception as exc:
        return _result(False, error=f"Invalid path: {exc}")

    if _is_restricted_path(target):
        return _result(False, error=f"Restricted path is not available through read-only MCP: {target}")
    if _is_secret_file(target):
        return _result(False, error=f"Secret-like files are blocked from read-only MCP: {target.name}")
    if not target.exists():
        return _result(False, error=f"File does not exist: {target}")
    if not target.is_file():
        return _result(False, error=f"Path is not a file: {target}")

    try:
        size = target.stat().st_size
        truncated = size > read_limit
        with target.open("rb") as handle:
            raw = handle.read(read_limit)
        text = raw.decode("utf-8", errors="replace")
        return _result(
            True,
            {
                "path": str(target),
                "size_bytes": size,
                "read_bytes": len(raw),
                "truncated": truncated,
                "content": text,
            },
        )
    except Exception as exc:
        return _result(False, error=f"Failed to read file: {exc}")


TOOL_REGISTRY = {
    "system_get_metrics_snapshot": system_get_metrics_snapshot,
    "system_list_processes": system_list_processes,
    "system_get_top_memory_processes": system_get_top_memory_processes,
    "network_list_connections": network_list_connections,
    "filesystem_list_directory": filesystem_list_directory,
    "filesystem_read_file": filesystem_read_file,
    "system_get_platform_info": system_get_platform_info,
}


def list_tool_names() -> list[str]:
    """Return supported local read-only MCP tool names."""
    return sorted(TOOL_REGISTRY.keys())

