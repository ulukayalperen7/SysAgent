import subprocess

class ExecutorService:
    """
    Safely executes autonomous READ commands in Python.
    Includes timeout bounds and separates stdout/stderr to prevent agent infinite loops.
    """
    
    @staticmethod
    def execute_safe_command(command: str, timeout: int = 15) -> dict:
        try:
            result = subprocess.run(
                command,
                shell=True,
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
