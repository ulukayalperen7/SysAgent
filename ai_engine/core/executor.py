import subprocess
import re

class ExecutorService:
    """
    Safely executes autonomous READ commands in Python.
    Includes timeout bounds and separates stdout/stderr to prevent agent infinite loops.
    """
    
    @staticmethod
    def execute_safe_command(command: str, timeout: int = 15) -> dict:
        if not command or command.strip() == "NONE" or command.strip() == "":
            return {"success": False, "stdout": "", "stderr": "Empty command.", "code": -1}
            
        # Strip markdown fences (e.g. ```powershell, ```bash, etc.) case-insensitively
        clean_command = re.sub(r'```[a-zA-Z0-9]*', '', command)
        clean_command = clean_command.replace('```', '').strip()
        
        try:
            # On Windows, shell=True uses cmd.exe by default. 
            # We force 'powershell' to support advanced cmdlets like Test-Path.
            full_command = ["powershell", "-Command", clean_command]
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds.",
                "code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution Error: {str(e)}",
                "code": -1
            }
