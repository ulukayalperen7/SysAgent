"""Read-only local system capabilities for the SysAgent MCP layer."""

from __future__ import annotations

import os
import platform
import socket
import fnmatch
from pathlib import Path
from typing import Any

import psutil

MAX_DIRECTORY_ENTRIES = 200
MAX_FILE_READ_BYTES = 200_000
MAX_PROCESS_LIMIT = 100
MAX_NETWORK_LIMIT = 100
MAX_SEARCH_RESULTS = 100
MAX_APP_LIMIT = 200
MAX_WALK_ENTRIES = 5_000
MAX_WALK_DEPTH = 6

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


def system_list_installed_apps(query: str | None = None, limit: int = 100) -> dict[str, Any]:
    """Discover launchable local applications from read-only OS locations."""
    app_limit = _bounded_int(limit, 100, MAX_APP_LIMIT)
    query_text = _normalize_app_query(query)
    apps_by_key: dict[str, dict[str, Any]] = {}

    for app in _iter_start_menu_apps():
        _add_app(apps_by_key, app, query_text, app_limit)
        if len(apps_by_key) >= app_limit:
            break

    if len(apps_by_key) < app_limit and os.name == "nt":
        for app in _iter_windows_app_paths():
            _add_app(apps_by_key, app, query_text, app_limit)
            if len(apps_by_key) >= app_limit:
                break

    if len(apps_by_key) < app_limit:
        for app in _iter_path_executables():
            _add_app(apps_by_key, app, query_text, app_limit)
            if len(apps_by_key) >= app_limit:
                break

    apps = sorted(apps_by_key.values(), key=lambda item: item["name"].lower())
    return _result(
        True,
        {
            "count": len(apps),
            "query": query,
            "truncated": len(apps) >= app_limit,
            "apps": apps,
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


def _iter_start_menu_apps() -> list[dict[str, Any]]:
    if os.name != "nt":
        return []

    start_roots = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]
    apps: list[dict[str, Any]] = []
    for root in start_roots:
        if not root.exists():
            continue
        try:
            for shortcut in root.rglob("*.lnk"):
                apps.append(
                    {
                        "name": shortcut.stem,
                        "source": "start_menu",
                        "launch_target": str(shortcut),
                        "launch_kind": "shortcut",
                    }
                )
        except (OSError, PermissionError):
            continue
    return apps


def _iter_windows_app_paths() -> list[dict[str, Any]]:
    if os.name != "nt":
        return []

    try:
        import winreg
    except ImportError:
        return []

    roots = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths"),
    ]
    apps: list[dict[str, Any]] = []
    for hive, subkey in roots:
        try:
            with winreg.OpenKey(hive, subkey) as root_key:
                for index in range(winreg.QueryInfoKey(root_key)[0]):
                    child_name = winreg.EnumKey(root_key, index)
                    try:
                        with winreg.OpenKey(root_key, child_name) as child_key:
                            target, _ = winreg.QueryValueEx(child_key, "")
                    except OSError:
                        target = child_name
                    apps.append(
                        {
                            "name": Path(child_name).stem,
                            "source": "app_paths",
                            "launch_target": target,
                            "launch_kind": "executable",
                        }
                    )
        except OSError:
            continue
    return apps


def _iter_path_executables() -> list[dict[str, Any]]:
    extensions = [".exe", ".cmd", ".bat"] if os.name == "nt" else [""]
    apps: list[dict[str, Any]] = []
    seen_dirs: set[str] = set()
    for raw_dir in os.environ.get("PATH", "").split(os.pathsep):
        if not raw_dir:
            continue
        directory = Path(os.path.expandvars(os.path.expanduser(raw_dir)))
        key = str(directory).lower()
        if key in seen_dirs or not directory.exists() or not directory.is_dir():
            continue
        seen_dirs.add(key)
        try:
            for entry in directory.iterdir():
                if entry.is_dir():
                    continue
                if os.name == "nt" and entry.suffix.lower() not in extensions:
                    continue
                if os.name != "nt" and not os.access(entry, os.X_OK):
                    continue
                apps.append(
                    {
                        "name": entry.stem if os.name == "nt" else entry.name,
                        "source": "path",
                        "launch_target": str(entry),
                        "launch_kind": "executable",
                    }
                )
        except (OSError, PermissionError):
            continue
    return apps


def _add_app(apps_by_key: dict[str, dict[str, Any]], app: dict[str, Any], query_text: str, limit: int) -> None:
    name = str(app.get("name", "")).strip()
    target = str(app.get("launch_target", "")).strip()
    if not name or not target:
        return
    if query_text and query_text not in _normalize_app_query(name) and query_text not in _normalize_app_query(target):
        return
    key = _normalize_app_query(f"{name}|{target}")
    if key in apps_by_key or len(apps_by_key) >= limit:
        return
    apps_by_key[key] = app


def _normalize_app_query(value: str | None) -> str:
    if not value:
        return ""
    translation = str.maketrans(
        {
            "\u00e7": "c",
            "\u011f": "g",
            "\u0131": "i",
            "\u00f6": "o",
            "\u015f": "s",
            "\u00fc": "u",
            "\u00c7": "c",
            "\u011e": "g",
            "\u0130": "i",
            "\u00d6": "o",
            "\u015e": "s",
            "\u00dc": "u",
        }
    )
    return value.translate(translation).lower().strip()


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


def network_list_interfaces() -> dict[str, Any]:
    """List local network interfaces, addresses, and link stats."""
    try:
        addresses = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
    except Exception as exc:
        return _result(False, error=f"Failed to read network interfaces: {exc}")

    interfaces: list[dict[str, Any]] = []
    for name, addr_list in sorted(addresses.items(), key=lambda item: item[0].lower()):
        stat = stats.get(name)
        interface_addresses = []
        for addr in addr_list:
            family = getattr(addr.family, "name", str(addr.family))
            interface_addresses.append(
                {
                    "family": family,
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast,
                }
            )
        interfaces.append(
            {
                "name": name,
                "is_up": bool(stat.isup) if stat else None,
                "speed_mbps": stat.speed if stat else None,
                "mtu": stat.mtu if stat else None,
                "addresses": interface_addresses,
            }
        )

    return _result(True, {"count": len(interfaces), "interfaces": interfaces})


def system_get_disk_partitions() -> dict[str, Any]:
    """List local mounted disk partitions and usage metadata."""
    partitions = []
    try:
        raw_partitions = psutil.disk_partitions(all=False)
    except Exception as exc:
        return _result(False, error=f"Failed to read disk partitions: {exc}")

    for partition in raw_partitions:
        usage_data: dict[str, Any] | None = None
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            usage_data = {
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent": usage.percent,
            }
        except Exception:
            usage_data = None

        partitions.append(
            {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "opts": partition.opts,
                "usage": usage_data,
            }
        )

    return _result(True, {"count": len(partitions), "partitions": partitions})


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


def filesystem_search(path: str | None = None, pattern: str = "*", limit: int = 50, max_depth: int = 4) -> dict[str, Any]:
    """Search a safe local directory tree with bounded depth and result count."""
    result_limit = _bounded_int(limit, 50, MAX_SEARCH_RESULTS)
    depth_limit = _bounded_int(max_depth, 4, MAX_WALK_DEPTH)

    try:
        root = _resolve_user_path(path)
    except Exception as exc:
        return _result(False, error=f"Invalid path: {exc}")

    if _is_restricted_path(root):
        return _result(False, error=f"Restricted path is not available through read-only MCP: {root}")
    if not root.exists():
        return _result(False, error=f"Search root does not exist: {root}")
    if not root.is_dir():
        return _result(False, error=f"Search root is not a directory: {root}")

    matches: list[dict[str, Any]] = []
    visited = 0
    try:
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            if _relative_depth(root, current_path) > depth_limit:
                dirs[:] = []
                continue

            dirs[:] = [
                directory
                for directory in dirs
                if not _is_restricted_path(current_path / directory) and not _is_secret_file(current_path / directory)
            ]

            for name in sorted([*dirs, *files], key=str.lower):
                if visited >= MAX_WALK_ENTRIES or len(matches) >= result_limit:
                    break
                visited += 1
                item = current_path / name
                if _is_secret_file(item):
                    continue
                if fnmatch.fnmatch(name.lower(), pattern.lower()):
                    try:
                        stat = item.stat()
                        matches.append(
                            {
                                "name": item.name,
                                "path": str(item),
                                "type": "directory" if item.is_dir() else "file",
                                "size_bytes": stat.st_size if item.is_file() else None,
                                "modified_epoch": stat.st_mtime,
                            }
                        )
                    except (OSError, PermissionError):
                        matches.append({"name": item.name, "path": str(item), "type": "unavailable"})
            if visited >= MAX_WALK_ENTRIES or len(matches) >= result_limit:
                break
    except Exception as exc:
        return _result(False, error=f"Filesystem search failed: {exc}")

    return _result(
        True,
        {
            "path": str(root),
            "pattern": pattern,
            "count": len(matches),
            "visited_entries": visited,
            "truncated": visited >= MAX_WALK_ENTRIES or len(matches) >= result_limit,
            "matches": matches,
        },
    )


def filesystem_get_disk_usage(path: str | None = None, max_entries: int = MAX_WALK_ENTRIES) -> dict[str, Any]:
    """Estimate bounded disk usage for a safe local directory tree."""
    walk_limit = _bounded_int(max_entries, MAX_WALK_ENTRIES, MAX_WALK_ENTRIES)

    try:
        root = _resolve_user_path(path)
    except Exception as exc:
        return _result(False, error=f"Invalid path: {exc}")

    if _is_restricted_path(root):
        return _result(False, error=f"Restricted path is not available through read-only MCP: {root}")
    if not root.exists():
        return _result(False, error=f"Path does not exist: {root}")

    if root.is_file():
        if _is_secret_file(root):
            return _result(False, error=f"Secret-like files are blocked from read-only MCP: {root.name}")
        return _result(True, {"path": str(root), "total_bytes": root.stat().st_size, "file_count": 1, "directory_count": 0, "truncated": False})

    total_bytes = 0
    file_count = 0
    directory_count = 0
    visited = 0

    try:
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            dirs[:] = [directory for directory in dirs if not _is_restricted_path(current_path / directory)]
            directory_count += len(dirs)

            for name in files:
                if visited >= walk_limit:
                    break
                visited += 1
                item = current_path / name
                if _is_secret_file(item):
                    continue
                try:
                    total_bytes += item.stat().st_size
                    file_count += 1
                except (OSError, PermissionError):
                    continue
            if visited >= walk_limit:
                break
    except Exception as exc:
        return _result(False, error=f"Disk usage scan failed: {exc}")

    return _result(
        True,
        {
            "path": str(root),
            "total_bytes": total_bytes,
            "file_count": file_count,
            "directory_count": directory_count,
            "visited_entries": visited,
            "truncated": visited >= walk_limit,
        },
    )


def _relative_depth(root: Path, path: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return MAX_WALK_DEPTH + 1


TOOL_REGISTRY = {
    "system_get_metrics_snapshot": system_get_metrics_snapshot,
    "system_list_installed_apps": system_list_installed_apps,
    "system_list_processes": system_list_processes,
    "system_get_top_memory_processes": system_get_top_memory_processes,
    "network_list_connections": network_list_connections,
    "network_list_interfaces": network_list_interfaces,
    "system_get_disk_partitions": system_get_disk_partitions,
    "filesystem_list_directory": filesystem_list_directory,
    "filesystem_read_file": filesystem_read_file,
    "filesystem_search": filesystem_search,
    "filesystem_get_disk_usage": filesystem_get_disk_usage,
    "system_get_platform_info": system_get_platform_info,
}


def list_tool_names() -> list[str]:
    """Return supported local read-only MCP tool names."""
    return sorted(TOOL_REGISTRY.keys())
