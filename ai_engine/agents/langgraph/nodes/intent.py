from langchain_core.messages import HumanMessage
from core.agent_state import AgentState
from .base import _get_langchain_llm

def detect_intent_node(state: AgentState):
    """
    Determines the Intent of the current active input.
    """
    llm = _get_langchain_llm()
    current_input = state.get("user_input")
    
    prompt = f"""
    You are an intent classifier for an Enterprise AI Agent. 
    Classify the incoming user input into EXACTLY ONE of these categories:
    - FILE_SYSTEM_READ (Listing files, viewing text files, searching for files)
    - FILE_SYSTEM_WRITE (Creating, deleting, modifying, moving files or folders) 
    - APP_CONTROL (Opening, closing, managing desktop applications)
    - DEVOPS_READ (Checking git status, docker ps, reading code)
    - DEVOPS_WRITE (git push, npm install, docker restart)
    - SYSTEM_OPERATION (Queries about OS stats, RAM, CPU, killing OS processes)
    - NETWORK_READ (Ping, port scanning)
    - CHAT (Greetings, casual talk)
    - UNKNOWN (If it doesn't clearly fit)
    
    User Input: {current_input}
    
    Output ONLY THE EXACT CATEGORY STRING.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    content_raw = response.content
    if isinstance(content_raw, list):
        content_str = content_raw[0].get("text", "") if len(content_raw) > 0 and isinstance(content_raw[0], dict) else str(content_raw[0]) if len(content_raw) > 0 else ""
    else:
        content_str = str(content_raw)
        
    intent = content_str.strip().upper()
    
    valid_intents = [
        "FILE_SYSTEM_READ", "FILE_SYSTEM_WRITE", "APP_CONTROL", 
        "DEVOPS_READ", "DEVOPS_WRITE", "SYSTEM_OPERATION", "NETWORK_READ", "CHAT"
    ]
    if intent not in valid_intents:
        intent = "UNKNOWN"
        
    return {"current_intent": intent}
