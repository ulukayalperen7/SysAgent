from __future__ import annotations

import base64
import platform
import subprocess


SCRIPT_TIMEOUT_SECONDS = 90
MAX_OUTPUT_CHARS = 120_000

BLOCKED_PATTERNS = (
    "rm -rf /",
    "mkfs",
    "dd if=",
    "shutdown",
    "reboot",
    "del /s /q c:\\",
    "format c:",
    ":(){:|:&};:",
)


def validate_script(script: str) -> str | None:
    lowered = (script or "").lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lowered:
            return f"Blocked local node command pattern: {pattern}"
    return None


def execute_script(script: str, timeout_seconds: int = SCRIPT_TIMEOUT_SECONDS) -> dict[str, object]:
    block_reason = validate_script(script)
    if block_reason:
        return {"success": False, "output": "", "error": block_reason}

    if platform.system().lower().startswith("win"):
        command = _powershell_command(script)
    else:
        command = ["bash", "-c", script]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Script timed out after {timeout_seconds} seconds."}
    except OSError as exc:
        return {"success": False, "output": "", "error": str(exc)}

    output = _truncate((completed.stdout or "").strip())
    error = _truncate((completed.stderr or "").strip())
    return {
        "success": completed.returncode == 0,
        "output": output,
        "error": error if completed.returncode != 0 else None,
    }


def _powershell_command(script: str) -> list[str]:
    wrapped = "$ErrorActionPreference = 'Stop'\ntry {\n" + script + "\n} catch {\nWrite-Error $_\nexit 1\n}"
    encoded = base64.b64encode(wrapped.encode("utf-16le")).decode("ascii")
    return ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-EncodedCommand", encoded]


def _truncate(value: str) -> str:
    return value if len(value) <= MAX_OUTPUT_CHARS else value[:MAX_OUTPUT_CHARS]
