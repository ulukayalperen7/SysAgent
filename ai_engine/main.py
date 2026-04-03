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

class AnalyzeRequest(BaseModel):
    user_prompt: str
    metrics: Dict[str, Any]

class AnalyzeResponse(BaseModel):
    status: str
    reply: str
    original_prompt: str

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_system(request: AnalyzeRequest):
    """
    Endpoint for Java Backend to send system metrics and user prompts for AI analysis.
    """
    try:
        # Step 1: Sanitize the user prompt (Security Layer)
        sanitized_prompt = SecurityAnalyzer.sanitize_prompt(request.user_prompt)
        
        # Step 2: Initialize the CrewAI Team
        crew_instance = SystemDiagnosticsCrew()
        inputs = {
            'metrics': str(request.metrics),
            'user_prompt': sanitized_prompt,
            'os_type': request.metrics.get('osName', 'Unknown OS')
        }
        
        # Step 3: Run the crew processes
        result = crew_instance.crew().kickoff(inputs=inputs)
        
        return AnalyzeResponse(
            status="success",
            reply=str(result),
            original_prompt=sanitized_prompt
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal AI Engine Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.debug_mode
    )
