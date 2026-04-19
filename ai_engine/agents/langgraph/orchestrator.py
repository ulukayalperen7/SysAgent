from langgraph.graph import StateGraph, START, END
from core.agent_state import AgentState
from agents.langgraph.nodes import (
    decompose_task_node,
    pop_next_task_node,
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
builder.add_node("decompose_task_node", decompose_task_node)
builder.add_node("pop_next_task_node", pop_next_task_node)
builder.add_node("detect_intent_node", detect_intent_node)
builder.add_node("direct_chat_node", direct_chat_node)
builder.add_node("run_crewai_diagnostics_node", run_crewai_diagnostics_node)
builder.add_node("generate_action_script_node", generate_action_script_node)
builder.add_node("execute_safe_action_node", execute_safe_action_node)

# 3. Define Flow
builder.add_edge(START, "decompose_task_node")
builder.add_edge("decompose_task_node", "pop_next_task_node")

def route_after_pop(state: AgentState):
    if not state.get("user_input"):
        return END # Queue empty
    return "detect_intent_node"

builder.add_conditional_edges(
    "pop_next_task_node",
    route_after_pop,
    {
        END: END,
        "detect_intent_node": "detect_intent_node"
    }
)

def route_after_intent(state: AgentState):
    intent = state.get("current_intent", "UNKNOWN")
    if intent == "CHAT":
        return "direct_chat_node"
    elif intent == "SYSTEM_OPERATION":
        return "run_crewai_diagnostics_node" 
    else:
        return "generate_action_script_node"

def route_after_script_generation(state: AgentState):
    script = state.get("script", "NONE")
    intent = state.get("current_intent", "UNKNOWN")
    
    if not script or script == "NONE":
        return "pop_next_task_node" # Skip to next step
        
    if SecurityGuardian.requires_approval(intent):
        return END # Halt for UI approval
    else:
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
        "execute_safe_action_node": "execute_safe_action_node",
        "pop_next_task_node": "pop_next_task_node"
    }
)

# Loop back edges
builder.add_edge("execute_safe_action_node", "pop_next_task_node")
builder.add_edge("direct_chat_node", "pop_next_task_node")
builder.add_edge("run_crewai_diagnostics_node", "pop_next_task_node")


from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
# 4. Compile Graph into Runnable Application with persistence
orchestrator_graph = builder.compile(checkpointer=memory)
