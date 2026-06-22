"""
main.py — FastAPI entry point for the SysAgent AI Engine.

Updated to use LangGraph Orchestrator as the primary intelligent router,
managing the interaction between Intent Nodes, Direct Chat, and CrewAI Tools.
"""
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any

from core.config import settings
from core.agent_hub import get_agent_hub_config, record_agent_decision_audit, reload_agent_hub_config
from core.langgraph_checkpoint import checkpoint_status
from core.mcp_client import local_system_mcp_client
from core.mcp_process import ensure_local_mcp_server
from core.runtime_health import runtime_health_status
from core.screen_context import prepare_device_context_for_graph, redact_device_context_for_audit, verify_action_outcome
from core.security import SecurityAnalyzer
from core.security_guardian import SecurityGuardian

app = FastAPI(
    title="SysAgent AI Engine",
    description="Multi-Agent AI Endpoint with LangGraph Orchestrator",
    version="2.0.0"
)

_orchestrator_graph = None


@app.middleware("http")
async def require_ai_engine_key(request: Request, call_next):
    if settings.api_key:
        provided = request.headers.get("X-SysAgent-AI-Key", "")
        if provided != settings.api_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid AI Engine API key."})
    return await call_next(request)


@app.on_event("startup")
async def startup_mcp_server():
    ensure_local_mcp_server()


@app.get("/mcp/status")
async def mcp_status():
    status = local_system_mcp_client.status()
    return {
        "available": status.available,
        "mode": status.mode,
        "detail": status.detail,
        "host": settings.mcp_host,
        "port": settings.mcp_port,
        "path": settings.mcp_path,
        "tools": local_system_mcp_client.list_tools(),
    }


@app.get("/agent-hub/status")
async def agent_hub_status(refresh: bool = False):
    config = reload_agent_hub_config() if refresh else get_agent_hub_config()
    payload = config.to_dict()
    payload["checkpoint"] = checkpoint_status()
    return payload


@app.get("/runtime/status")
async def runtime_status(refresh_agent_hub: bool = False):
    config = reload_agent_hub_config() if refresh_agent_hub else get_agent_hub_config()
    mcp = local_system_mcp_client.status()
    return {
        "runtime": runtime_health_status(),
        "agent_hub": {
            "source": config.source,
            "route_count": len(config.routes),
            "prompt_agents": sorted(config.prompts.keys()),
        },
        "checkpoint": checkpoint_status(),
        "mcp": {
            "available": mcp.available,
            "mode": mcp.mode,
            "detail": mcp.detail,
            "tools": local_system_mcp_client.list_tools(),
        },
        "screen_context": {
            "vision_enabled": settings.screen_vision_enabled,
            "vision_model": settings.llm_model,
            "max_base64_chars": settings.screen_vision_max_base64_chars,
            "raw_images_retained_in_graph_state": False,
        },
    }

class AnalyzeRequest(BaseModel):
    task_id: str | None = None
    thread_id: str = "default_thread_1" # Injected by Java Backend for isolated sessions
    owner_id: str | None = None
    target_device_id: int | None = None
    device_context: Dict[str, Any] = Field(default_factory=dict)
    user_prompt: str
    metrics: Dict[str, Any]

class AnalyzeResponse(BaseModel):
    status: str
    reply: str
    explanation: str
    script: str
    original_prompt: str
    active_step: str | None = None
    pending_count: int = 0  # Number of tasks remaining in the execution queue

class VerifyActionRequest(BaseModel):
    task_id: str | None = None
    expected_action: str
    command_output: str | None = None
    command_error: str | None = None
    device_context: Dict[str, Any] = Field(default_factory=dict)

class VerifyActionResponse(BaseModel):
    task_id: str | None = None
    status: str
    reason: str
    screen_summary: str | None = None

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_system(request: AnalyzeRequest):
    sanitized_prompt = SecurityAnalyzer.sanitize_prompt(request.user_prompt)

    try:
        device_context = prepare_device_context_for_graph(
            request.device_context or {"execution_mode": "local_backend"}
        )
        # Prepare the state for the LangGraph execution
        initial_state = {
            "thread_id": request.thread_id,
            "owner_id": request.owner_id,
            "target_device_id": request.target_device_id,
            "device_context": device_context,
            "user_input": sanitized_prompt,
            "metrics": request.metrics,
            "os_type": request.metrics.get("osName", "Unknown OS"),
            "messages": [{"role": "user", "content": sanitized_prompt}], # Preserved + Appended by Reducer
            "explanation": "", # Clear any previous explanation loop aggregation
            "script": "NONE",
            "mcp_tools_used": [],
            "errors": [],
            "retry_count": 0
        }
        
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Invoke the robust LangGraph orchestrator
        final_state = get_orchestrator_graph().invoke(initial_state, config)
        current_intent = final_state.get("current_intent", "UNKNOWN")
        selected_route = get_agent_hub_config().select_route(
            current_intent,
            final_state.get("user_input") or sanitized_prompt,
        )
        script = final_state.get("script", "NONE")
        approval_required = bool(script and script != "NONE" and SecurityGuardian.requires_approval(current_intent))
        record_agent_decision_audit(
            task_id=request.task_id,
            thread_id=request.thread_id,
            owner_id=request.owner_id,
            intent_key=current_intent,
            agent_slug=_agent_slug_for_route(selected_route.target_langgraph_node if selected_route else None),
            mcp_tools_used=final_state.get("mcp_tools_used", []),
            approval_required=approval_required,
            decision_summary=(final_state.get("explanation", "") or "")[:500],
            raw_metadata={
                "agent_hub_source": get_agent_hub_config().source,
                "route_type": selected_route.route_type if selected_route else None,
                "target_langgraph_node": selected_route.target_langgraph_node if selected_route else None,
                "script_proposed": bool(script and script != "NONE"),
                "pending_count": len(final_state.get("task_queue", [])),
                "target_device_id": request.target_device_id,
                "device_context": redact_device_context_for_audit(device_context),
            },
        )
        
        pending_count = len(final_state.get("task_queue", []))
        return AnalyzeResponse(
            status="success",
            reply=final_state.get("explanation", "No explanation provided."),
            explanation=final_state.get("explanation", "No explanation provided."),
            script=final_state.get("script", "NONE"),
            original_prompt=sanitized_prompt,
            active_step=final_state.get("user_input") or sanitized_prompt,
            pending_count=pending_count
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


@app.post("/verify-action", response_model=VerifyActionResponse)
async def verify_action(request: VerifyActionRequest):
    device_context = prepare_device_context_for_graph(
        request.device_context or {"execution_mode": "local_backend"}
    )
    verification = verify_action_outcome(
        expected_action=request.expected_action,
        command_output=request.command_output,
        command_error=request.command_error,
        prepared_device_context=device_context,
    )
    return VerifyActionResponse(
        task_id=request.task_id,
        status=verification.get("status") or "uncertain",
        reason=verification.get("reason") or "Verification did not produce a reason.",
        screen_summary=verification.get("screen_summary"),
    )


def _agent_slug_for_route(target_langgraph_node: str | None) -> str | None:
    return {
        "direct_chat_node": "direct_chat_agent",
        "mcp_read_only_node": "mcp_read_agent",
        "run_crewai_diagnostics_node": "crewai_diagnostics_agent",
        "generate_action_script_node": "script_proposal_agent",
    }.get(target_langgraph_node or "")


def get_orchestrator_graph():
    """Load the LangGraph app lazily so status endpoints survive missing deps."""
    global _orchestrator_graph
    if _orchestrator_graph is None:
        from agents.langgraph.graphs.orchestrator import orchestrator_graph

        _orchestrator_graph = orchestrator_graph
    return _orchestrator_graph

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug_mode
    )
