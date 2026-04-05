"""
main.py — FastAPI entry point for the SysAgent AI Engine.

Receives analysis requests from the Java backend and routes them through
the CrewAI pipeline. Includes a fast-path classifier that intercepts simple
conversational messages (greetings, thanks, etc.) before they hit the LLM
pipeline, reducing average response time for non-system queries to <100ms.

"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from core.config import settings
from core.security import SecurityAnalyzer
from agents.crewai.crew import SystemDiagnosticsCrew

app = FastAPI(
    title="SysAgent AI Engine",
    description="Multi-Agent AI Endpoint for System Diagnostics",
    version="1.0.0"
)

# Semaphore ensures only one crew runs at a time.
# The LLM is stateful during a run — concurrent calls cause race conditions.
_crew_semaphore = asyncio.Semaphore(1)

# Simple patterns that never need the full 4-agent pipeline.
# Matching any of these triggers an instant response without calling the LLM.
CHAT_TRIGGERS = {
    "hi", "hello", "hey", "hi there", "howdy",
    "thanks", "thank you", "thank u", "ty",
    "ok", "okay", "okey", "k", "got it",
    "bye", "goodbye", "cya", "see ya",
    "good morning", "good afternoon", "good evening", "good night"
}


class AnalyzeRequest(BaseModel):
    user_prompt: str
    metrics: Dict[str, Any]


class AnalyzeResponse(BaseModel):
    status: str
    reply: str
    original_prompt: str


def _is_casual_chat(prompt: str) -> bool:
    """
    Returns True if the prompt is a simple greeting or acknowledgement.
    These messages are intercepted before the crew pipeline to save 30-60 seconds.
    """
    normalized = prompt.strip().lower().rstrip("!.,?")
    return normalized in CHAT_TRIGGERS


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_system(request: AnalyzeRequest):
    """
    Receives a user prompt and system metrics from the Java backend.
    Routes simple chat messages instantly; sends real queries through the CrewAI pipeline.
    """
    # Step 1: Sanitize the incoming prompt
    sanitized_prompt = SecurityAnalyzer.sanitize_prompt(request.user_prompt)

    # Step 2: Fast-path — respond immediately to casual conversation
    if _is_casual_chat(sanitized_prompt):
        return AnalyzeResponse(
            status="success",
            reply="Explanation: Hi! SysAgent is actively monitoring your system. How can I help?\nScript: NONE",
            original_prompt=sanitized_prompt
        )

    # Step 3: Acquire semaphore before running the crew (prevents concurrent crew runs)
    if _crew_semaphore.locked():
        # Another request is already being processed — tell the user to wait
        return AnalyzeResponse(
            status="success",
            reply="Explanation: SysAgent is already processing a request. Please wait a moment and try again.\nScript: NONE",
            original_prompt=sanitized_prompt
        )

    async with _crew_semaphore:
        try:
            crew_instance = SystemDiagnosticsCrew()
            inputs = {
                "metrics": str(request.metrics),
                "user_prompt": sanitized_prompt,
                "os_type": request.metrics.get("osName", "Unknown OS")
            }

            # Run the blocking crew pipeline in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: crew_instance.crew().kickoff(inputs=inputs)
            )

            return AnalyzeResponse(
                status="success",
                reply=str(result),
                original_prompt=sanitized_prompt
            )

        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug_mode
    )
