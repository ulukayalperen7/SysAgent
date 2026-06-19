import operator
from typing import TypedDict, Annotated, List, Dict, Any, NotRequired

class AgentState(TypedDict):
    """
    Core state object for the SysAgent LangGraph Orchestrator.
    This defines the memory schema passed between all nodes.
    """
    # Unique identifier for isolated user sessions (e.g., node_id + user_id)
    thread_id: str

    # Auth/device context supplied by the Spring API boundary.
    owner_id: NotRequired[str | None]
    target_device_id: NotRequired[int | None]
    device_context: NotRequired[Dict[str, Any]]
    
    # Input variables
    user_input: str
    
    # History with reducer (Annotated[list, operator.add]) ensures new messages are APPENDED, not overwritten
    messages: Annotated[list, operator.add]
    
    # System Context Variables
    metrics: Dict[str, Any]
    os_type: str
    
    # State tracking
    current_intent: str
    task_queue: List[str]
    mcp_tools_used: Annotated[List[str], operator.add]
    
    # Output variables corresponding to the API contract
    explanation: str
    script: str
    
    # Error management
    errors: List[str]
    retry_count: int
