"""Script proposal, risk validation, and rollback helpers for SysAgent."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["Low", "Medium", "High"]


@dataclass(frozen=True)
class ScriptProposal:
    """A generated command plus user-facing safety metadata."""

    explanation: str
    script: str
    risk_level: RiskLevel
    rollback: str


@dataclass(frozen=True)
class CommandRisk:
    """Result of command risk validation before frontend approval."""

    allowed: bool
    risk_level: RiskLevel
    reason: str
    rollback: str


def propose_deterministic_script(user_input: str, intent: str, os_name: str) -> ScriptProposal | None:
    """
    Generate reliable scripts for common terminal operations without relying on an LLM.

    The function only proposes commands. It never executes anything. Risky
    operations still go to Angular for approval and Spring Boot for execution.
    """
    if "win" not in os_name.lower():
        return _propose_unix_script(user_input, intent)
    return _propose_windows_script(user_input, intent)


def validate_command_risk(command: str, intent: str, os_name: str) -> CommandRisk:
    """Classify command risk and provide a concise rollback note."""
    lower = command.lower()
    risk: RiskLevel = "Low"
    reasons: list[str] = []

    if intent in {"FILE_SYSTEM_WRITE", "DEVOPS_WRITE", "APP_CONTROL", "UNKNOWN"}:
        risk = "Medium"
        reasons.append("This request can change local system state.")

    high_markers = [
        "remove-item",
        "rm ",
        "del ",
        "stop-process",
        "taskkill",
        "winget uninstall",
        "uninstall",
        "format",
        "erase",
    ]
    if any(marker in lower for marker in high_markers):
        risk = "High"
        reasons.append("The command can delete data, stop processes, or uninstall software.")

    if any(marker in lower for marker in ("winget install", "npm install", "pip install", "docker run", "docker compose")):
        risk = "Medium" if risk != "High" else risk
        reasons.append("The command can install or start external software.")

    rollback = suggest_rollback(command, intent)
    reason = " ".join(reasons) if reasons else "Read-like or low-impact command proposal."
    return CommandRisk(allowed=True, risk_level=risk, reason=reason, rollback=rollback)


def format_terminal_proposal(proposal: ScriptProposal) -> str:
    """Format risky-action output consistently for the terminal."""
    return (
        "Understanding:\n"
        f"{proposal.explanation}\n\n"
        "Proposed Action:\n"
        "I prepared a local script for your review. It will not run until you approve it.\n\n"
        "Risk Level:\n"
        f"{proposal.risk_level}\n\n"
        "Rollback:\n"
        f"{proposal.rollback}"
    )


def suggest_rollback(command: str, intent: str) -> str:
    """Return a practical rollback note without pretending all operations are reversible."""
    lower = command.lower()
    if "new-item" in lower and "itemtype file" in lower:
        return "Created files can usually be removed manually if the path is correct."
    if "set-content" in lower or "add-content" in lower:
        return "File writes overwrite or append content; keep a backup if the file already exists."
    if "remove-item" in lower or re.search(r"\brm\b|\bdel\b", lower):
        return "Deletion may not be reversible unless the file is recoverable from backup or recycle bin."
    if "stop-process" in lower or "taskkill" in lower:
        return "Closed applications can usually be reopened, but unsaved work may be lost."
    if "winget uninstall" in lower or "uninstall" in lower:
        return "Uninstalled applications usually require reinstalling from the original source."
    if "winget install" in lower or "npm install" in lower or "pip install" in lower:
        return "Installed packages may need manual uninstall if the result is unwanted."
    return "No automatic rollback is available; review the script before approval."


def _propose_windows_script(user_input: str, intent: str) -> ScriptProposal | None:
    lower = user_input.lower()

    if _is_media_next(lower):
        return ScriptProposal(
            explanation="You want to send the global media next-track key.",
            script=_windows_media_key_script("0xB0"),
            risk_level="Medium",
            rollback="No rollback is needed; this only sends a media key event.",
        )

    if _is_media_previous(lower):
        return ScriptProposal(
            explanation="You want to send the global media previous-track key.",
            script=_windows_media_key_script("0xB1"),
            risk_level="Medium",
            rollback="No rollback is needed; this only sends a media key event.",
        )

    if _is_media_play_pause(lower):
        return ScriptProposal(
            explanation="You want to toggle media play/pause.",
            script=_windows_media_key_script("0xB3"),
            risk_level="Medium",
            rollback="Run the same action again to toggle play/pause back.",
        )

    if intent == "APP_CONTROL" and _looks_like_close_app(lower):
        app = _extract_app_name(user_input, close=True)
        if app:
            process = _sanitize_process_name(app)
            return ScriptProposal(
                explanation=f"You want to close the local application/process named '{process}'.",
                script=f'Stop-Process -Name "{process}" -Force -ErrorAction Stop',
                risk_level="High",
                rollback="Closed applications can usually be reopened, but unsaved work may be lost.",
            )

    if intent == "APP_CONTROL" and _looks_like_open_app(lower):
        app = _extract_app_name(user_input, close=False)
        if app:
            clean_app = _sanitize_app_name(app)
            script = (
                f'$app = "{clean_app}"\n'
                "$candidates = @($app, \"$app.exe\", \"${app}:\")\n"
                "$started = $false\n"
                "foreach ($candidate in $candidates) {\n"
                "  try { Start-Process $candidate -ErrorAction Stop; $started = $true; break } catch { }\n"
                "}\n"
                "if (-not $started) { throw \"Could not start application: $app\" }"
            )
            return ScriptProposal(
                explanation=f"You want to open the local application '{clean_app}'.",
                script=script,
                risk_level="Medium",
                rollback="Close the application if it was opened by mistake.",
            )

    if intent == "FILE_SYSTEM_WRITE":
        file_name = _extract_file_name(user_input)
        target_dir = _windows_target_directory(user_input)
        if file_name and _looks_like_delete_file(lower):
            script = (
                f"$targetDir = {target_dir}\n"
                f'$path = Join-Path $targetDir "{file_name}"\n'
                'if (-not (Test-Path -LiteralPath $path)) { throw "File not found: $path" }\n'
                "Remove-Item -LiteralPath $path -Force -ErrorAction Stop"
            )
            return ScriptProposal(
                explanation=f"You want to delete '{file_name}' from the selected local folder.",
                script=script,
                risk_level="High",
                rollback="Deletion may not be reversible unless the file is recoverable from backup or recycle bin.",
            )

        if file_name and _looks_like_write_file(lower):
            content = _extract_quoted_content(user_input) or ""
            script = (
                f"$targetDir = {target_dir}\n"
                f'$path = Join-Path $targetDir "{file_name}"\n'
                f'Set-Content -LiteralPath $path -Value "{_escape_powershell_double_quoted(content)}" -Encoding UTF8 -Force -ErrorAction Stop'
            )
            return ScriptProposal(
                explanation=f"You want to write text into '{file_name}' in the selected local folder.",
                script=script,
                risk_level="Medium",
                rollback="File writes may overwrite existing content; restore from backup if needed.",
            )

        if file_name and _looks_like_create_file(lower):
            script = (
                f"$targetDir = {target_dir}\n"
                f'$path = Join-Path $targetDir "{file_name}"\n'
                'if (Test-Path -LiteralPath $path) { throw "File already exists: $path" }\n'
                'New-Item -ItemType File -Path $path -ErrorAction Stop | Out-Null'
            )
            return ScriptProposal(
                explanation=f"You want to create '{file_name}' in the selected local folder.",
                script=script,
                risk_level="Medium",
                rollback="Remove the created file if it was created by mistake.",
            )

    if intent == "DEVOPS_WRITE" or _looks_like_install_or_uninstall(lower):
        app = _extract_app_name(user_input, close=False)
        if app and any(term in lower for term in ("uninstall", "remove app", "uygulama sil", "kaldır")):
            clean_app = _sanitize_app_name(app)
            return ScriptProposal(
                explanation=f"You want to uninstall the local application/package '{clean_app}'.",
                script=f'winget uninstall --name "{clean_app}"',
                risk_level="High",
                rollback="Uninstalled applications usually require reinstalling from the original source.",
            )
        if app and any(term in lower for term in ("install", "yükle", "kur")):
            clean_app = _sanitize_app_name(app)
            return ScriptProposal(
                explanation=f"You want to install the application/package '{clean_app}'.",
                script=f'winget install --name "{clean_app}"',
                risk_level="Medium",
                rollback="Installed applications can usually be removed with winget uninstall.",
            )

    return None


def _propose_unix_script(user_input: str, intent: str) -> ScriptProposal | None:
    lower = user_input.lower()
    if intent == "APP_CONTROL" and _looks_like_close_app(lower):
        app = _extract_app_name(user_input, close=True)
        if app:
            process = _sanitize_process_name(app)
            return ScriptProposal(
                explanation=f"You want to close the local application/process named '{process}'.",
                script=f'pkill -f "{process}"',
                risk_level="High",
                rollback="Closed applications can usually be reopened, but unsaved work may be lost.",
            )
    if intent == "APP_CONTROL" and _looks_like_open_app(lower):
        app = _extract_app_name(user_input, close=False)
        if app:
            clean_app = _sanitize_app_name(app)
            return ScriptProposal(
                explanation=f"You want to open the local application '{clean_app}'.",
                script=f'nohup "{clean_app}" >/dev/null 2>&1 &',
                risk_level="Medium",
                rollback="Close the application if it was opened by mistake.",
            )
    return None


def _windows_media_key_script(virtual_key: str) -> str:
    return (
        'Add-Type -TypeDefinition @"\n'
        "using System;\n"
        "using System.Runtime.InteropServices;\n"
        "public class SysAgentMediaKeys {\n"
        '  [DllImport("user32.dll")]\n'
        "  public static extern void keybd_event(byte bVk, byte bScan, int dwFlags, UIntPtr dwExtraInfo);\n"
        "}\n"
        '"@\n'
        f"[SysAgentMediaKeys]::keybd_event({virtual_key}, 0, 0, [UIntPtr]::Zero)\n"
        f"[SysAgentMediaKeys]::keybd_event({virtual_key}, 0, 2, [UIntPtr]::Zero)"
    )


def _looks_like_open_app(lower: str) -> bool:
    return any(term in lower for term in ("open ", "launch ", "start ", "aç", "ac "))


def _looks_like_close_app(lower: str) -> bool:
    return any(term in lower for term in ("close ", "quit ", "kill ", "kapat", "sonlandır"))


def _is_media_next(lower: str) -> bool:
    return any(term in lower for term in ("next song", "next track", "skip song", "diğer şarkı", "sonraki şarkı", "siradaki sarki"))


def _is_media_previous(lower: str) -> bool:
    return any(term in lower for term in ("previous song", "previous track", "önceki şarkı", "onceki sarki"))


def _is_media_play_pause(lower: str) -> bool:
    return any(term in lower for term in ("play pause", "pause", "resume music", "duraklat", "devam ettir"))


def _looks_like_create_file(lower: str) -> bool:
    return any(term in lower for term in ("create", "touch", "oluştur", "olustur"))


def _looks_like_write_file(lower: str) -> bool:
    return any(term in lower for term in ("write", "set content", "put text", "yaz"))


def _looks_like_delete_file(lower: str) -> bool:
    return any(term in lower for term in ("delete", "remove", "sil"))


def _looks_like_install_or_uninstall(lower: str) -> bool:
    return any(term in lower for term in ("install", "uninstall", "yükle", "kur", "kaldır", "uygulama sil"))


def _extract_app_name(text: str, close: bool) -> str | None:
    verbs = "close|quit|kill|kapat|sonlandır" if close else "open|launch|start|aç|ac|install|uninstall|yükle|kur|kaldır"
    match = re.search(rf"(?:{verbs})\s+['\"]?([A-Za-z0-9_.+ -]{{2,80}})['\"]?", text, re.IGNORECASE)
    if not match:
        return None
    app = match.group(1).strip(" .")
    app = re.split(r"\s+(?:then|sonra|and then|ardından)\s+", app, maxsplit=1, flags=re.IGNORECASE)[0]
    return app.strip() or None


def _extract_file_name(text: str) -> str | None:
    quoted = re.search(r"['\"]([^'\"]+\.[A-Za-z0-9]{1,8})['\"]", text)
    if quoted:
        return _sanitize_file_name(quoted.group(1))
    match = re.search(r"([A-Za-z0-9_. -]+\.[A-Za-z0-9]{1,8})", text)
    if match:
        return _sanitize_file_name(match.group(1).strip())
    return None


def _extract_quoted_content(text: str) -> str | None:
    quoted = re.findall(r"['\"]([^'\"]+)['\"]", text)
    if not quoted:
        return None
    if len(quoted) == 1 and re.search(r"\.[A-Za-z0-9]{1,8}$", quoted[0]):
        return None
    # If a quoted filename and quoted content both exist, the last quoted value is the content.
    return quoted[-1]


def _windows_target_directory(text: str) -> str:
    lower = text.lower()
    if "download" in lower:
        return "[Environment]::GetFolderPath('UserProfile') + '\\Downloads'"
    if "document" in lower:
        return "[Environment]::GetFolderPath('MyDocuments')"
    return "[Environment]::GetFolderPath('Desktop')"


def _sanitize_app_name(app: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.+ -]", "", app).strip()


def _sanitize_process_name(process: str) -> str:
    cleaned = _sanitize_app_name(process)
    return re.sub(r"\.exe$", "", cleaned, flags=re.IGNORECASE)


def _sanitize_file_name(file_name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", file_name).strip()


def _escape_powershell_double_quoted(value: str) -> str:
    return value.replace("`", "``").replace('"', '`"').replace("$", "`$")
