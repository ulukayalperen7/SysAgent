"""
response_parse.py — Utilities for splitting raw CrewAI string output into 
human-readable explanation and executable script components.

Expects the LLM to follow the "Explanation: ... Script: ..." format defined 
in the task configurations.
"""

import re
from typing import Tuple

def parse_explanation_and_script(raw_result: str) -> Tuple[str, str]:
    """
    Parses a raw string from the AI pipeline into (explanation, script).
    Returns ("NONE", "NONE") if parsing fails or result is empty.
    """
    if not raw_result:
        return "No response from AI.", "NONE"

    # Default values
    explanation = "Detailed analysis completed by SysAgent AI."
    script = "NONE"

    # Strict parsing based on keywords
    if "Explanation:" in raw_result and "Script:" in raw_result:
        try:
            # Split by 'Script:' to separate the two parts
            parts = raw_result.split("Script:", 1)
            explanation = parts[0].replace("Explanation:", "").strip()
            script = parts[1].strip()
        except Exception:
            # Fallback if structure is slightly distorted
            explanation = raw_result.strip()
    else:
        # If the LLM failed to follow the format, treat the whole thing as explanation
        explanation = raw_result.strip()

    return explanation, script
