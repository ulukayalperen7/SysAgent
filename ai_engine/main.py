"""
main.py — FastAPI entry point for the SysAgent AI Engine.

Updated to use LangGraph Orchestrator as the primary intelligent router,
managing the interaction between Intent Nodes, Direct Chat, and CrewAI Tools.
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from core.config import settings
from core.security import SecurityAnalyzer
from agents.langgraph.orchestrator import orchestrator_graph

app = FastAPI(
    title="SysAgent AI Engine",
    description="Multi-Agent AI Endpoint with LangGraph Orchestrator",
    version="2.0.0"
)

class AnalyzeRequest(BaseModel):
    thread_id: str = "default_thread_1" # Injected by Java Backend for isolated sessions
    user_prompt: str
    metrics: Dict[str, Any]

class AnalyzeResponse(BaseModel):
    status: str
    reply: str
    explanation: str
    script: str
    original_prompt: str

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_system(request: AnalyzeRequest):
    sanitized_prompt = SecurityAnalyzer.sanitize_prompt(request.user_prompt)

    try:
        # Prepare the state for the LangGraph execution
        initial_state = {
            "thread_id": request.thread_id,
            "user_input": sanitized_prompt,
            "metrics": request.metrics,
            "os_type": request.metrics.get("osName", "Unknown OS"),
            "messages": [{"role": "user", "content": sanitized_prompt}], # Preserved + Appended by Reducer
            "explanation": "", # Clear any previous explanation loop aggregation
            "script": "NONE",
            "errors": []
        }
        
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Invoke the robust LangGraph orchestrator
        final_state = orchestrator_graph.invoke(initial_state, config)
        
        return AnalyzeResponse(
            status="success",
            reply=final_state.get("explanation", "No explanation provided."),
            explanation=final_state.get("explanation", "No explanation provided."),
            script=final_state.get("script", "NONE"),
            original_prompt=sanitized_prompt
        )

    except Exception as e:
        err_msg = f"AI Graph Orchestrator Error: {str(e)}"
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
