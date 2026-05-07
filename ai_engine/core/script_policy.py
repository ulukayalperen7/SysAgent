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


def propose_deterministic_script(
    user_input: str,
    intent: str,
    os_name: str,
    context_messages: list[dict] | None = None,
) -> ScriptProposal | None:
    """
    Generate reliable scripts for common terminal operations without relying on an LLM.

    The function only proposes commands. It never executes anything. Risky
    operations still go to Angular for approval and Spring Boot for execution.
    """
    if "win" not in os_name.lower():
        return _propose_unix_script(user_input, intent)
    return _propose_windows_script(user_input, intent, context_messages)


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


def _propose_windows_script(
    user_input: str,
    intent: str,
    context_messages: list[dict] | None = None,
) -> ScriptProposal | None:
    lower = _normalize_for_matching(user_input)

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
        app = _resolve_app_reference(
            _extract_app_name(user_input, close=False),
            user_input,
            context_messages,
        )
        if app:
            clean_app = _sanitize_app_name(app)
            script = _windows_open_app_script(clean_app)
            return ScriptProposal(
                explanation=f"You want to open the local application '{clean_app}'.",
                script=script,
                risk_level="Medium",
                rollback="Close the application if it was opened by mistake.",
            )

    if intent == "FILE_SYSTEM_WRITE":
        file_name = _extract_file_name(user_input)
        if not file_name and _looks_like_contextual_file_write(lower):
            file_name = _extract_recent_file_name(context_messages)
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
            content = _extract_write_content(user_input, file_name)
            content = _expand_code_write_request(user_input, file_name, content)
            script = _windows_set_content_script(target_dir, file_name, content)
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
    lower = _normalize_for_matching(user_input)
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


def _windows_open_app_script(app: str) -> str:
    safe_app = _escape_powershell_double_quoted(app)
    return (
        f'$app = "{safe_app}"\n'
        "function Normalize-Name([string]$value) {\n"
        "  if ([string]::IsNullOrWhiteSpace($value)) { return '' }\n"
        "  return (($value -replace '[^a-zA-Z0-9]', '').ToLowerInvariant())\n"
        "  }\n"
        "$needle = Normalize-Name $app\n"
        "$fallbackProcess = ($app -replace '\\.exe$', '')\n"
        "$candidates = New-Object System.Collections.Generic.List[object]\n"
        "function Add-Candidate([string]$target, [string[]]$processNames) {\n"
        "  if ([string]::IsNullOrWhiteSpace($target)) { return }\n"
        "  foreach ($existing in $candidates) { if ($existing.Target -eq $target) { return } }\n"
        "  $candidates.Add([pscustomobject]@{ Target = $target; ProcessNames = $processNames }) | Out-Null\n"
        "}\n"
        "function Matches-App([string]$value) {\n"
        "  $normalized = Normalize-Name $value\n"
        "  return $normalized -and ($normalized.Contains($needle) -or $needle.Contains($normalized))\n"
        "}\n"
        "function Test-AppRunning([string[]]$processNames) {\n"
        "  foreach ($name in $processNames) {\n"
        "    if ($name -and (Get-Process -Name $name -ErrorAction SilentlyContinue)) { return $true }\n"
        "  }\n"
        "  foreach ($proc in Get-Process -ErrorAction SilentlyContinue) {\n"
        "    $procName = Normalize-Name $proc.ProcessName\n"
        "    if ($procName -and ($procName.Contains($needle) -or $needle.Contains($procName))) { return $true }\n"
        "  }\n"
        "  return $false\n"
        "}\n"
        "Add-Candidate $app @($fallbackProcess)\n"
        "Add-Candidate \"$app.exe\" @($fallbackProcess)\n"
        "$appPathRoots = @(\n"
        "  'Registry::HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\App Paths',\n"
        "  'Registry::HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\App Paths',\n"
        "  'Registry::HKEY_LOCAL_MACHINE\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\App Paths'\n"
        ")\n"
        "foreach ($root in $appPathRoots) {\n"
        "  try {\n"
        "    foreach ($item in Get-ChildItem $root -ErrorAction Stop) {\n"
        "      $target = (Get-Item -LiteralPath $item.PSPath -ErrorAction SilentlyContinue).GetValue('')\n"
        "      $leaf = [IO.Path]::GetFileNameWithoutExtension($item.PSChildName)\n"
        "      if ((Matches-App $item.PSChildName) -or (Matches-App $leaf) -or (Matches-App $target)) {\n"
        "        $proc = if ($target) { [IO.Path]::GetFileNameWithoutExtension($target) } else { $leaf }\n"
        "        if ($target) { Add-Candidate $target @($proc) } else { Add-Candidate $item.PSChildName @($proc) }\n"
        "      }\n"
        "    }\n"
        "  } catch { }\n"
        "}\n"
        "$startMenus = @(\n"
        "  [Environment]::GetFolderPath('StartMenu'),\n"
        "  [Environment]::GetFolderPath('CommonStartMenu')\n"
        ")\n"
        "$shell = $null\n"
        "try { $shell = New-Object -ComObject WScript.Shell } catch { }\n"
        "foreach ($menu in $startMenus) {\n"
        "  if (-not (Test-Path -LiteralPath $menu)) { continue }\n"
        "  foreach ($shortcut in Get-ChildItem -LiteralPath $menu -Filter *.lnk -Recurse -ErrorAction SilentlyContinue) {\n"
        "    if (-not (Matches-App $shortcut.BaseName)) { continue }\n"
        "    $procNames = @($fallbackProcess)\n"
        "    if ($shell) {\n"
        "      try {\n"
        "        $targetPath = $shell.CreateShortcut($shortcut.FullName).TargetPath\n"
        "        if ($targetPath) { $procNames = @([IO.Path]::GetFileNameWithoutExtension($targetPath), $fallbackProcess) }\n"
        "      } catch { }\n"
        "    }\n"
        "    Add-Candidate $shortcut.FullName $procNames\n"
        "  }\n"
        "}\n"
        "try {\n"
        "  foreach ($startApp in Get-StartApps -ErrorAction Stop) {\n"
        "    if (Matches-App $startApp.Name) {\n"
        "      Add-Candidate \"shell:AppsFolder\\$($startApp.AppID)\" @($fallbackProcess)\n"
        "    }\n"
        "  }\n"
        "} catch { }\n"
        "try {\n"
        "  foreach ($protocol in Get-ChildItem 'Registry::HKEY_CLASSES_ROOT' -ErrorAction Stop) {\n"
        "    try {\n"
        "      $props = Get-ItemProperty -LiteralPath $protocol.PSPath -ErrorAction Stop\n"
        "      $label = (Get-Item -LiteralPath $protocol.PSPath -ErrorAction SilentlyContinue).GetValue('')\n"
        "      if ($null -ne $props.'URL Protocol' -and ((Matches-App $protocol.PSChildName) -or (Matches-App $label))) {\n"
        "        Add-Candidate \"$($protocol.PSChildName):\" @($fallbackProcess)\n"
        "      }\n"
        "    } catch { }\n"
        "  }\n"
        "} catch { }\n"
        "if (Test-AppRunning @($fallbackProcess)) { return }\n"
        "$started = $false\n"
        "foreach ($candidate in $candidates) {\n"
        "  try {\n"
        "    Start-Process $candidate.Target -ErrorAction Stop | Out-Null\n"
        "    Start-Sleep -Seconds 3\n"
        "    if (Test-AppRunning $candidate.ProcessNames) { $started = $true; break }\n"
        "  } catch { }\n"
        "}\n"
        "if (-not $started) { throw \"Could not start application or verify process: $app\" }"
    )


def _looks_like_open_app(lower: str) -> bool:
    if re.search(r"\b(ac|calistir|baslat)\b", lower):
        return True
    return any(term in lower for term in ("open ", "launch ", "start ", "aç", "ac "))


def _looks_like_close_app(lower: str) -> bool:
    if re.search(r"\b(kapat|sonlandir)\b", lower):
        return True
    return any(term in lower for term in ("close ", "quit ", "kill ", "kapat", "sonlandır"))


def _is_media_next(lower: str) -> bool:
    if any(term in lower for term in ("diger sarki", "sonraki sarki", "sarki atla", "ileri sar")):
        return True
    return any(term in lower for term in ("next song", "next track", "skip song", "diğer şarkı", "sonraki şarkı", "siradaki sarki"))


def _is_media_previous(lower: str) -> bool:
    if any(term in lower for term in ("onceki sarki", "geri sar")):
        return True
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
        trailing_app = _extract_app_before_trailing_verb(text, close)
        if trailing_app:
            return _strip_turkish_object_suffix(trailing_app)
        return None
    app = match.group(1).strip(" .")
    app = re.split(r"\s+(?:then|sonra|and then|ardından)\s+", app, maxsplit=1, flags=re.IGNORECASE)[0]
    return _strip_turkish_object_suffix(app.strip()) or None


def _resolve_app_reference(app: str | None, text: str, context_messages: list[dict] | None) -> str | None:
    """Resolve pronouns like "open it again" to a concrete recent app name."""
    if app and not _is_app_pronoun(app):
        return app

    mentioned = _extract_app_mentioned_before_reference(text)
    if mentioned:
        return mentioned

    return _extract_recent_app_name(context_messages)


def _is_app_pronoun(app: str) -> bool:
    normalized = _normalize_for_matching(app).strip(" .'\"")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized in {"it", "it again", "again", "that", "that app", "this", "this app", "onu", "bunu"}


def _extract_app_mentioned_before_reference(text: str) -> str | None:
    """Handle prompts like "I closed spotify, can you open it again"."""
    patterns = [
        r"\b(?:closed|close|kapat(?:tim|tım)?|kapattim)\s+['\"]?([A-Za-z0-9_.+ -]{2,80})['\"]?",
        r"\b(?:opened|open|actim|açtım)\s+['\"]?([A-Za-z0-9_.+ -]{2,80})['\"]?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        candidate = match.group(1).strip(" .")
        candidate = re.split(
            r"\s+(?:can|could|please|pls|and|then|sonra|open|close|again|it|onu|bunu)\b",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        cleaned = _sanitize_app_name(_strip_turkish_object_suffix(candidate))
        if cleaned and not _is_app_pronoun(cleaned):
            return cleaned
    return None


def _extract_recent_app_name(context_messages: list[dict] | None) -> str | None:
    if not context_messages:
        return None

    patterns = [
        r"local application ['\"]([^'\"]+)['\"]",
        r"application/process named ['\"]([^'\"]+)['\"]",
        r"\$app\s*=\s*['\"]([^'\"]+)['\"]",
    ]
    for message in reversed(context_messages[-12:]):
        content = str(message.get("content", ""))
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                cleaned = _sanitize_app_name(match.group(1))
                if cleaned and not _is_app_pronoun(cleaned):
                    return cleaned
    return None


def _extract_app_before_trailing_verb(text: str, close: bool) -> str | None:
    """Support Turkish order such as "spotify ac" or "notepad kapat"."""
    normalized = _normalize_for_matching(text)
    verbs = ("kapat", "sonlandir") if close else ("ac", "calistir", "baslat", "yukle", "kur")
    for verb in verbs:
        match = re.search(rf"^\s*([A-Za-z0-9_.+' -]{{2,80}}?)\s+{verb}\b", normalized)
        if match:
            # Normalization maps Turkish characters one-for-one, so indexes can
            # slice the original text without shifting the app name.
            app = text[match.start(1) : match.end(1)].strip(" .")
            return app or None
    return None


def _strip_turkish_object_suffix(app: str) -> str:
    """Remove Turkish object particles from app names, e.g. "spotify'i ac"."""
    cleaned = app.strip(" .'\"")
    cleaned = re.sub(r"(?:['\s]+)(?:i|ı|u|ü|yi|yı|yu|yü)$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" .'\"")


def _extract_file_name(text: str) -> str | None:
    quoted = re.search(r"['\"]([^'\"]+\.[A-Za-z0-9]{1,8})['\"]", text)
    if quoted:
        return _sanitize_file_name(quoted.group(1))

    # Match one filename token only. Allowing spaces here made Turkish location
    # words such as "masaüstüne deneme.txt" leak into the filename.
    match = re.search(r"(?<![\w.-])([A-Za-z0-9_-]+\.[A-Za-z0-9]{1,8})(?![\w.-])", text)
    if match:
        return _sanitize_file_name(match.group(1).strip())
    return None


def _extract_write_content(text: str, file_name: str) -> str:
    """Extract user text for file write commands, including Turkish follow-ups."""
    quoted_content = _extract_quoted_content(text)
    if quoted_content is not None:
        return quoted_content

    normalized = _normalize_for_matching(text)
    for marker in ("icine", "into it", "inside it", "dosyaya"):
        marker_index = normalized.find(marker)
        if marker_index >= 0:
            # Turkish follow-ups often say "write this into it" without naming
            # the file again. Normalization preserves indexes one-for-one.
            content = text[marker_index + len(marker) :]
            return _clean_write_content(content)

    lower = text.lower()
    if "içine" in lower or "icine" in lower:
        content = re.split(r"\biçine\b|\bicine\b", text, maxsplit=1, flags=re.IGNORECASE)[-1]
        content = re.sub(r"\byaz(?:sana)?\b", "", content, flags=re.IGNORECASE)
        return _clean_write_content(content)

    content = re.sub(re.escape(file_name), "", text, flags=re.IGNORECASE)
    content = re.sub(
        r"\b(write|yaz|to|into|inside|file|dosya|dosyaya|içine|icine|tamam)\b",
        "",
        content,
        flags=re.IGNORECASE,
    )
    return _clean_write_content(content)


def _extract_quoted_content(text: str) -> str | None:
    quoted = re.findall(r"['\"]([^'\"]+)['\"]", text)
    if not quoted:
        return None
    if len(quoted) == 1 and re.search(r"\.[A-Za-z0-9]{1,8}$", quoted[0]):
        return None
    # If a quoted filename and quoted content both exist, the last quoted value is the content.
    return quoted[-1]


def _looks_like_contextual_file_write(lower: str) -> bool:
    """Detect follow-up writes that refer to the most recently mentioned file."""
    return _looks_like_write_file(lower) and any(
        term in lower for term in ("içine", "icine", "into it", "inside it", "dosyaya")
    )


def _extract_recent_file_name(context_messages: list[dict] | None) -> str | None:
    """Find the latest filename mentioned in recent LangGraph conversation state."""
    if not context_messages:
        return None

    for message in reversed(context_messages[-12:]):
        content = str(message.get("content", ""))
        matches = re.findall(r"(?<![\w.-])([A-Za-z0-9_-]+\.[A-Za-z0-9]{1,8})(?![\w.-])", content)
        if matches:
            return _sanitize_file_name(matches[-1])
    return None


def _clean_write_content(content: str) -> str:
    """Remove command words that are not meant to become file content."""
    cleaned = content.strip(" .")
    for filler in ("yaz", "yazsana", "tamam", "onun", "ona", "bunun", "sunun", "\u015funun"):
        cleaned = re.sub(rf"\b{re.escape(filler)}\b", "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", cleaned).strip(" .")


def _expand_code_write_request(text: str, file_name: str, content: str) -> str:
    """
    Turn common "write simple code" requests into useful starter code.

    This keeps the terminal practical: a user asking for FastAPI code in a .py
    file expects runnable scaffolding, not the literal words "simple FastAPI code".
    """
    lower = _normalize_for_matching(text)
    if file_name.lower().endswith(".py") and ("fastapi" in lower or "fast api" in lower):
        return (
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n\n"
            '@app.get("/")\n'
            "def read_root():\n"
            '    return {"message": "Hello from SysAgent"}\n'
        )
    return content


def _windows_set_content_script(target_dir: str, file_name: str, content: str) -> str:
    """Build a PowerShell write script that safely handles multiline content."""
    safe_content = content.replace("\r\n", "\n").replace("\r", "\n")
    safe_content = safe_content.replace("\n'@\n", "\n' + '@\n")
    return (
        f"$targetDir = {target_dir}\n"
        f'$path = Join-Path $targetDir "{file_name}"\n'
        "$content = @'\n"
        f"{safe_content}\n"
        "'@\n"
        "Set-Content -LiteralPath $path -Value $content -Encoding UTF8 -Force -ErrorAction Stop"
    )


def _windows_target_directory(text: str) -> str:
    lower = _normalize_for_matching(text)
    if "download" in lower:
        return "[Environment]::GetFolderPath('UserProfile') + '\\\\Downloads'"
    if "document" in lower:
        return "[Environment]::GetFolderPath('MyDocuments')"
    if "desktop" in lower or "masaustu" in lower:
        return "[Environment]::GetFolderPath('Desktop')"
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


def _normalize_for_matching(text: str) -> str:
    """Lowercase and fold Turkish characters so intent matching is stable."""
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
    return text.translate(translation).lower()
