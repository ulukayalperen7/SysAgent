"""
tools.py - CrewAI Tool Definitions for the SysAgent AI Engine.

Each function decorated with @tool becomes an executable capability
that agents can invoke during their reasoning process. Tools are
read-only by design — they observe the system, never modify it.
Date: 2026-04-04
"""

from crewai.tools import tool
import psutil


# ---------------------------------------------------------------------------
# Tool 1: System Audit Tool
# Purpose: Returns the top 10 RAM-consuming processes on the host OS.
# Owner:   Log Investigator agent
# ---------------------------------------------------------------------------

@tool("System Audit Tool")
def system_audit_tool(query: str) -> str:
    """
    Scans the live host operating system for running processes,
    memory usage, and CPU percentages to investigate a performance problem.
    If a query string is provided (e.g., 'spotify'), it will also specifically 
    search for and include processes matching that name.
    Returns the top 10 heaviest processes plus any specific matches found.
    """
    processes = []
    search_matches = []
    search_query = query.lower() if query and query.strip() != "None" else None

    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            name = proc.info['name']
            mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
            p_data = {
                'pid': proc.info['pid'],
                'name': name,
                'memory_mb': round(mem_mb, 2),
                'cpu_percent': proc.info['cpu_percent']
            }
            processes.append(p_data)
            
            # If we are searching for a specific process, check if it matches
            if search_query and search_query in name.lower():
                search_matches.append(p_data)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Rank by memory usage, heaviest first
    top_processes = sorted(processes, key=lambda x: x['memory_mb'], reverse=True)[:10]

    result = "TOP 10 PROCESSES BY RAM USAGE:\n"
    for p in top_processes:
        result += f"PID: {p['pid']} | Name: {p['name']} | RAM: {p['memory_mb']} MB | CPU: {p['cpu_percent']}%\n"

    if search_query and search_matches:
        result += f"\nMATCHES FOR SEARCH '{search_query}':\n"
        for p in search_matches[:5]: # Limit search matches to avoid context bloat
            result += f"PID: {p['pid']} | Name: {p['name']} | RAM: {p['memory_mb']} MB | CPU: {p['cpu_percent']}%\n"
    elif search_query:
        result += f"\nNO PROCESSES FOUND MATCHING '{search_query}'.\n"

    return result


# ---------------------------------------------------------------------------
# Tool 2: Network Audit Tool
# Purpose: Read-only snapshot of active TCP/UDP network connections.
#
# SAFETY CONTRACT:
#   - This tool ONLY reads. It will NEVER send packets, block connections,
#     kill sockets, or modify firewall rules.
#   - Designed to detect unexpected outbound connections and suspicious ports.
# Owner:   Log Investigator & Security Auditor agents
# ---------------------------------------------------------------------------

@tool("Network Audit Tool")
def network_audit_tool(query: str) -> str:
    """
    Captures a read-only snapshot of active network connections on the host.
    Identifies which processes are communicating, on which ports, and to
    which remote addresses. This tool NEVER modifies network state.
    """
    # Known safe/common ports — connections on these are expected
    COMMON_PORTS = {80, 443, 53, 8080, 8001, 4200, 5432, 3306, 22, 3389}

    # Common malware/RAT port ranges to flag for review
    SUSPICIOUS_PORTS = {1337, 4444, 6666, 6667, 31337, 12345, 5555}

    connections = []

    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.status != 'ESTABLISHED':
                # Only show active connections, not listening sockets
                continue

            remote_ip   = conn.raddr.ip if conn.raddr else "N/A"
            remote_port = conn.raddr.port if conn.raddr else 0
            local_port  = conn.laddr.port if conn.laddr else 0

            # Try to resolve the owning process name
            proc_name = "Unknown"
            if conn.pid:
                try:
                    proc_name = psutil.Process(conn.pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_name = f"PID {conn.pid} (no access)"

            # Flag the connection if it's on a known suspicious port
            flag = "[SUSPICIOUS PORT]" if remote_port in SUSPICIOUS_PORTS else ""

            connections.append({
                'process': proc_name,
                'pid': conn.pid,
                'local_port': local_port,
                'remote_ip': remote_ip,
                'remote_port': remote_port,
                'flag': flag
            })

    except Exception as e:
        return f"Network audit failed: {str(e)}"

    if not connections:
        return "No active ESTABLISHED connections found at this moment."

    result = f"ACTIVE NETWORK CONNECTIONS ({len(connections)} total):\n"
    for c in connections[:15]:  # Cap at 15 to avoid overwhelming the LLM context
        flag_str = f" {c['flag']}" if c['flag'] else ""
        result += (
            f"Process: {c['process']} (PID {c['pid']}) | "
            f"Local Port: {c['local_port']} → "
            f"Remote: {c['remote_ip']}:{c['remote_port']}{flag_str}\n"
        )

    return result


# ---------------------------------------------------------------------------
# Tool 3: Open App Tool
# Purpose: Launches a specific application on the host OS.
# Owner:   Log Investigator agent
# ---------------------------------------------------------------------------

@tool("Open App Tool")
def open_app_tool(app_name: str) -> str:
    """
    Launches a specific application (e.g., 'notepad', 'calc', 'chrome') 
    on the host operating system. This is a non-blocking operation.
    Returns a confirmation that the launch command was sent.
    """
    import subprocess
    import os

    # Basic normalization
    app = app_name.lower().strip().replace(".exe", "")
    
    try:
        # On Windows, 'start' is a shell command, so we use shell=True
        # We use Popen so we don't wait for the app to close
        subprocess.Popen(f"start {app}", shell=True)
        return f"SUCCESS: Sent command to launch '{app}'. The application should open shortly."
    except Exception as e:
        return f"ERROR: Failed to launch '{app}': {str(e)}"
