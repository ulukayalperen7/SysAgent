import operator
from typing import TypedDict, Annotated, List, Dict, Any

class AgentState(TypedDict):
    """
    Core state object for the SysAgent LangGraph Orchestrator.
    This defines the memory schema passed between all nodes.
    """
    # Unique identifier for isolated user sessions (e.g., node_id + user_id)
    thread_id: str
    
    # Input variables
    user_input: str
    
    # History with reducer (Annotated[list, operator.add]) ensures new messages are APPENDED, not overwritten
    messages: Annotated[list, operator.add]
    
    # System Context Variables
    metrics: Dict[str, Any]
    os_type: str
    
    # State tracking
    current_intent: str
    task_queue: List[Dict[str, Any]]
    
    # Output variables corresponding to the API contract
    explanation: str
    script: str
    
    # Error management
    errors: List[str]
