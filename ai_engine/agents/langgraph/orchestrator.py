from langgraph.graph import StateGraph, START, END
from core.agent_state import AgentState
from agents.langgraph.nodes import detect_intent_node, direct_chat_node, run_crewai_diagnostics_node

def route_intent(state: AgentState):
    """
    Conditional routing function used by LangGraph conditional edges.
    """
    intent = state.get("current_intent", "UNKNOWN")
    
    if intent == "CHAT" or intent == "UNKNOWN":
        return "direct_chat_node"
    elif intent == "SYSTEM_OPERATION":
        return "run_crewai_diagnostics_node"
    else:
        return "direct_chat_node"

# 1. Initialize StateGraph with our TypedDict State
builder = StateGraph(AgentState)

# 2. Add Nodes
builder.add_node("detect_intent_node", detect_intent_node)
builder.add_node("direct_chat_node", direct_chat_node)
builder.add_node("run_crewai_diagnostics_node", run_crewai_diagnostics_node)

# 3. Add Edges (Control Flow)
# The graph starts by analyzing the intent
builder.add_edge(START, "detect_intent_node")

# Routing Logic: From Intent Node -> target action node
builder.add_conditional_edges(
    "detect_intent_node",
    route_intent,
    {
        "direct_chat_node": "direct_chat_node",
        "run_crewai_diagnostics_node": "run_crewai_diagnostics_node"
    }
)

# Terminate after execution nodes
builder.add_edge("direct_chat_node", END)
builder.add_edge("run_crewai_diagnostics_node", END)

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
# 4. Compile Graph into Runnable Application with persistence
orchestrator_graph = builder.compile(checkpointer=memory)
