"""FastMCP server exposing SysAgent read-only local system tools."""

from __future__ import annotations

import argparse
import inspect
from typing import Any

from core.config import settings
from mcp_servers.local_system_tools import (
    devops_docker_ps as _devops_docker_ps,
    devops_git_status as _devops_git_status,
    devops_list_npm_scripts as _devops_list_npm_scripts,
    filesystem_list_directory as _filesystem_list_directory,
    filesystem_get_disk_usage as _filesystem_get_disk_usage,
    filesystem_read_file as _filesystem_read_file,
    filesystem_search as _filesystem_search,
    network_list_connections as _network_list_connections,
    network_list_interfaces as _network_list_interfaces,
    system_get_disk_partitions as _system_get_disk_partitions,
    system_list_installed_apps as _system_list_installed_apps,
    system_get_metrics_snapshot as _system_get_metrics_snapshot,
    system_get_platform_info as _system_get_platform_info,
    system_get_top_memory_processes as _system_get_top_memory_processes,
    system_list_processes as _system_list_processes,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment]


def build_server() -> Any:
    """Build the optional FastMCP server without making app imports depend on MCP."""
    if FastMCP is None:
        raise RuntimeError("MCP Python SDK is not installed. Install with: pip install 'mcp[cli]'")

    init_kwargs: dict[str, Any] = {
        "instructions": "Read-only local system inspection tools for SysAgent.",
        "json_response": True,
    }
    signature = inspect.signature(FastMCP)
    if "host" in signature.parameters:
        init_kwargs["host"] = settings.mcp_host
    if "port" in signature.parameters:
        init_kwargs["port"] = settings.mcp_port

    mcp = FastMCP("SysAgent Local System", **init_kwargs)

    @mcp.tool()
    def devops_git_status(path: str | None = None) -> dict[str, Any]:
        """Read git branch/status for a safe local repository path."""
        return _devops_git_status(path=path)

    @mcp.tool()
    def devops_docker_ps(limit: int = 50) -> dict[str, Any]:
        """Read running Docker containers without mutating Docker state."""
        return _devops_docker_ps(limit=limit)

    @mcp.tool()
    def devops_list_npm_scripts(path: str | None = None) -> dict[str, Any]:
        """Read package.json scripts from a safe local project path."""
        return _devops_list_npm_scripts(path=path)

    @mcp.tool()
    def system_get_metrics_snapshot() -> dict[str, Any]:
        """Return a read-only local CPU, memory, disk, and boot metrics snapshot."""
        return _system_get_metrics_snapshot()

    @mcp.tool()
    def system_list_installed_apps(query: str | None = None, limit: int = 100) -> dict[str, Any]:
        """Discover launchable local applications from read-only OS locations."""
        return _system_list_installed_apps(query=query, limit=limit)

    @mcp.tool()
    def system_list_processes(query: str | None = None, limit: int = 50) -> dict[str, Any]:
        """List local processes by optional name query."""
        return _system_list_processes(query=query, limit=limit)

    @mcp.tool()
    def system_get_top_memory_processes(limit: int = 10) -> dict[str, Any]:
        """Return top local processes sorted by resident memory usage."""
        return _system_get_top_memory_processes(limit=limit)

    @mcp.tool()
    def network_list_connections(limit: int = 50) -> dict[str, Any]:
        """List active local network connections without mutation."""
        return _network_list_connections(limit=limit)

    @mcp.tool()
    def network_list_interfaces() -> dict[str, Any]:
        """List local network interfaces, addresses, and link stats."""
        return _network_list_interfaces()

    @mcp.tool()
    def system_get_disk_partitions() -> dict[str, Any]:
        """List local mounted disk partitions and usage metadata."""
        return _system_get_disk_partitions()

    @mcp.tool()
    def filesystem_list_directory(path: str | None = None, limit: int = 100) -> dict[str, Any]:
        """List entries in a non-restricted local directory."""
        return _filesystem_list_directory(path=path, limit=limit)

    @mcp.tool()
    def filesystem_read_file(path: str, max_bytes: int = 200_000) -> dict[str, Any]:
        """Read a bounded non-secret local text file."""
        return _filesystem_read_file(path=path, max_bytes=max_bytes)

    @mcp.tool()
    def filesystem_search(path: str | None = None, pattern: str = "*", limit: int = 50, max_depth: int = 4) -> dict[str, Any]:
        """Search a non-restricted local directory tree with bounded output."""
        return _filesystem_search(path=path, pattern=pattern, limit=limit, max_depth=max_depth)

    @mcp.tool()
    def filesystem_get_disk_usage(path: str | None = None, max_entries: int = 5_000) -> dict[str, Any]:
        """Estimate disk usage for a non-restricted local path with bounded traversal."""
        return _filesystem_get_disk_usage(path=path, max_entries=max_entries)

    @mcp.tool()
    def system_get_platform_info() -> dict[str, Any]:
        """Return OS and Python runtime platform information."""
        return _system_get_platform_info()

    return mcp


def main() -> None:
    """Run the local system MCP server over the requested MCP transport."""
    parser = argparse.ArgumentParser(description="SysAgent local read-only MCP server")
    parser.add_argument("--transport", default=settings.mcp_transport)
    parser.add_argument("--host", default=settings.mcp_host)
    parser.add_argument("--port", type=int, default=settings.mcp_port)
    args = parser.parse_args()

    settings.mcp_host = args.host
    settings.mcp_port = args.port
    settings.mcp_transport = args.transport

    server = build_server()
    try:
        server.run(transport=args.transport)
    except TypeError:
        # Older MCP SDKs only support stdio run() without a transport parameter.
        server.run()


if __name__ == "__main__":
    main()
