"""
main.py — FastAPI entry point for the SysAgent AI Engine.

Updated to return structured JSON (explanation and script) to match the
Java backend's preferred communication contract.
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from core.config import settings
from core.security import SecurityAnalyzer
from core.response_parse import parse_explanation_and_script
from agents.crewai.crew import SystemDiagnosticsCrew

app = FastAPI(
    title="SysAgent AI Engine",
    description="Multi-Agent AI Endpoint for System Diagnostics",
    version="1.1.0"
)

# Semaphore ensures only one crew runs at a time.
_crew_semaphore = asyncio.Semaphore(1)

# Simple patterns that never need the full 4-agent pipeline.
CHAT_TRIGGERS = {
    "hi", "hello", "hey", "hi there", "howdy",
    "thanks", "thank you", "thank u", "ty",
    "ok", "okay", "okey", "k", "got it",
    "bye", "goodbye", "cya", "see ya",
    "good morning", "good afternoon", "good evening", "good night"
}


# Thread-safe global memory (sliding window of last 5 messages)
session_history = []


class AnalyzeRequest(BaseModel):
    user_prompt: str
    metrics: Dict[str, Any]


class AnalyzeResponse(BaseModel):
    status: str
    reply: str  # Kept for legacy compatibility
    explanation: str
    script: str
    original_prompt: str


def _is_casual_chat(prompt: str) -> bool:
    normalized = prompt.strip().lower().rstrip("!.,?")
    return normalized in CHAT_TRIGGERS


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_system(request: AnalyzeRequest):
    sanitized_prompt = SecurityAnalyzer.sanitize_prompt(request.user_prompt)

    # Fast-path for casual conversation
    if _is_casual_chat(sanitized_prompt):
        return AnalyzeResponse(
            status="success",
            reply=f"Explanation: Hello! How can I help you today?\nScript: NONE",
            explanation="Hello! How can I help you today?",
            script="NONE",
            original_prompt=sanitized_prompt
        )

    # Concurrent request protection
    if _crew_semaphore.locked():
        return AnalyzeResponse(
            status="success",
            reply="Explanation: Thinking... SysAgent is busy.\nScript: NONE",
            explanation="I'm currently thinking about another task. Please wait a moment.",
            script="NONE",
            original_prompt=sanitized_prompt
        )

    async with _crew_semaphore:
        try:
            # Build context from history
            history_str = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in session_history])

            # Optimize metrics
            m = request.metrics
            summarized_metrics = (
                f"CPU: {m.get('cpuUsage', 0)}%, "
                f"RAM: {m.get('ramUsage', 0)}% ({m.get('usedRam', 0)//(1024**2)}MB/{m.get('totalRam', 0)//(1024**2)}MB), "
                f"Disk: {m.get('usedDisk', 0)//(1024**3)}GB/{m.get('totalDisk', 0)//(1024**3)}GB"
            )

            crew_instance = SystemDiagnosticsCrew()
            inputs = {
                "metrics": summarized_metrics,
                "user_prompt": sanitized_prompt,
                "history": history_str,
                "os_type": m.get("osName", "Unknown OS")
            }

            # Run kickoff
            loop = asyncio.get_event_loop()
            raw_result = await loop.run_in_executor(
                None,
                lambda: str(crew_instance.crew().kickoff(inputs=inputs))
            )

            # Split fields
            explanation, script = parse_explanation_and_script(raw_result)

            # Update history (keep last 5)
            session_history.append({"user": sanitized_prompt, "ai": explanation})
            if len(session_history) > 5:
                session_history.pop(0)

            return AnalyzeResponse(
                status="success",
                reply=raw_result,
                explanation=explanation,
                script=script,
                original_prompt=sanitized_prompt
            )

        except Exception as e:
            # ENSURE we always return a structured response even on failure
            err_msg = f"AI Engine Error: {str(e)}"
            return AnalyzeResponse(
                status="error",
                reply=f"Explanation: {err_msg}\nScript: NONE",
                explanation=err_msg,
                script="NONE",
                original_prompt=sanitized_prompt
            )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug_mode
    )
