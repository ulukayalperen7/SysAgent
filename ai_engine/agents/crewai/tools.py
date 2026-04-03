from crewai.tools import tool
import psutil

@tool("System Audit Tool")
def system_audit_tool(query: str) -> str:
    """
    Scans the actual live host operating system for running background processes,
    memory usage, and CPU percentages to investigate a problem.
    """
    lowercase_query = query.lower()
    
    # Get the top 10 memory-consuming processes
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            # We fetch memory in MB
            mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'memory_mb': round(mem_mb, 2),
                'cpu_percent': proc.info['cpu_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Sort by memory usage descending
    processes = sorted(processes, key=lambda x: x['memory_mb'], reverse=True)
    top_processes = processes[:10]
    
    result = "TOP 10 PROCESSES CURRENTLY RUNNING:\n"
    for p in top_processes:
        result += f"PID: {p['pid']} | Name: {p['name']} | RAM: {p['memory_mb']} MB | CPU: {p['cpu_percent']}%\n"
        
    return result

@tool("Script Recommendation Tool")
def script_recommendation_tool(os_type: str, action: str) -> str:
    """
    Suggests the appropriate command line script for a desired action based on the OS.
    Never executes the command, just returns the formatted string for user review.
    """
    if "windows" in os_type.lower():
        if "close" in action.lower() or "kill" in action.lower():
            return "Stop-Process -Name 'ProcessName' -Force"
        if "clean temp" in action.lower():
            return "Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue"
        return f"# Windows script for: {action}"
    else:
        if "close" in action.lower() or "kill" in action.lower():
            return "pkill -f 'ProcessName'"
        if "clean temp" in action.lower():
            return "rm -rf /tmp/*"
        return f"# Unix/Linux script for: {action}"
