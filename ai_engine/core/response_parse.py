"""
Single place for turning Chief Reporter text into explanation + optional script.
Keeps behavior aligned with the Java adapter (strip fences, NONE handling).
"""

DEFAULT_EXPLANATION = "Detailed analysis completed by SysAgent AI."


def strip_code_fences(raw: str) -> str:
    return (
        raw.replace("```bash", "")
        .replace("```powershell", "")
        .replace("```", "")
        .strip()
    )


def parse_explanation_script(raw: str) -> tuple[str, str | None]:
    """
    Parses crew final output that uses 'Explanation:' and 'Script:' markers.
    If markers are missing, returns the full text as explanation and no script.
    """
    if not raw or not str(raw).strip():
        return DEFAULT_EXPLANATION, None
    s = str(raw).strip()
    if "Explanation:" in s and "Script:" in s:
        try:
            parts = s.split("Script:", 2)
            explanation = parts[0].replace("Explanation:", "").strip()
            raw_script = parts[1].strip() if len(parts) > 1 else ""
            if raw_script.upper() == "NONE" or not raw_script:
                return explanation or DEFAULT_EXPLANATION, None
            cleaned = strip_code_fences(raw_script)
            return explanation or DEFAULT_EXPLANATION, cleaned or None
        except Exception:
            return s, None
    return s, None
