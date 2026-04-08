from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# --- PIEPLINE CONTRACT MODELS ---
# These models enforce strict JSON outputs between agents to prevent hallucination.

class AnalysisOutput(BaseModel):
    """Structured output for User Intent Analysis."""
    intent: Literal["ACTION_CLOSE", "ACTION_OPEN", "INFO", "CHAT"] = Field(
        description="Categorized user intent retrieved from natural language."
    )
    target_apps: List[str] = Field(
        description="Target applications identified for operations."
    )
    goal_summary: str = Field(
        description="Context-aware summary of the user's objective."
    )

class DiagnosticOutput(BaseModel):
    """Structured output for System Facts gathering."""
    needs_action: bool = Field(
        description="Boolean flag indicating if a system change is required."
    )
    facts: str = Field(
        description="Raw tool output and gathered system facts."
    )
    target_pid: Optional[int] = Field(
        None, 
        description="PID of the target application found during audit."
    )
    app_found: bool = Field(
        default=True, 
        description="Status flag: False if the requested app is not running/found."
    )

class SecurityOutput(BaseModel):
    """Structured output for Risk Assessment."""
    risk_level: Literal["SAFE", "LOW_RISK", "REVIEW", "BLOCKED"] = Field(
        description="Determinant risk level for the proposed script execution."
    )
    justification: str = Field(
        description="Concise safety reasoning for the final report."
    )

