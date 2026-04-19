from langgraph.graph import StateGraph, START, END
from core.agent_state import AgentState
from agents.langgraph.nodes import (
    detect_intent_node, 
    direct_chat_node, 
    run_crewai_diagnostics_node,
    generate_action_script_node,
    execute_safe_action_node
)
from core.security_guardian import SecurityGuardian

# 1. Initialize StateGraph
builder = StateGraph(AgentState)

# 2. Add Nodes
builder.add_node("detect_intent_node", detect_intent_node)
builder.add_node("direct_chat_node", direct_chat_node)
builder.add_node("run_crewai_diagnostics_node", run_crewai_diagnostics_node)
builder.add_node("generate_action_script_node", generate_action_script_node)
builder.add_node("execute_safe_action_node", execute_safe_action_node)

# 3. Define Conditional Edges and Flow
builder.set_entry_point("detect_intent_node")

def route_after_intent(state: AgentState):
    intent = state.get("current_intent", "UNKNOWN")
    if intent == "CHAT":
        return "direct_chat_node"
    elif intent == "SYSTEM_OPERATION":
        return "run_crewai_diagnostics_node" 
    else:
        # DEVOPS, APP_CONTROL, FILE_SYSTEM, NETWORK, etc.
        return "generate_action_script_node"

def route_after_script_generation(state: AgentState):
    script = state.get("script", "NONE")
    intent = state.get("current_intent", "UNKNOWN")
    
    if not script or script == "NONE":
        return END # E.g., Blocked by security, or just not actionable
        
    if SecurityGuardian.requires_approval(intent):
        # Requires UI approval. END LangGraph directly.
        # Frontend sees the script and prompts User.
        return END 
    else:
        # Autonomous Read Node. Safe to execute instantly in Python.
        return "execute_safe_action_node"


builder.add_conditional_edges(
    "detect_intent_node",
    route_after_intent,
    {
        "direct_chat_node": "direct_chat_node",
        "run_crewai_diagnostics_node": "run_crewai_diagnostics_node",
        "generate_action_script_node": "generate_action_script_node"
    }
)

builder.add_conditional_edges(
    "generate_action_script_node",
    route_after_script_generation,
    {
        END: END,
        "execute_safe_action_node": "execute_safe_action_node"
    }
)

# Terminal edges for existing nodes
builder.add_edge("direct_chat_node", END)
builder.add_edge("run_crewai_diagnostics_node", END)
builder.add_edge("execute_safe_action_node", END)

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
# 4. Compile Graph into Runnable Application with persistence
orchestrator_graph = builder.compile(checkpointer=memory)
