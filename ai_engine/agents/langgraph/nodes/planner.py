import json
from langchain_core.messages import HumanMessage
from core.agent_state import AgentState
from .base import _get_langchain_llm

def decompose_task_node(state: AgentState):
    """
    Analyzes the user input and decomposes it into a list of atomic tasks.
    If the input is simple, it returns a single-item list.
    """
    user_msg = state.get("user_input", "").lower().strip()
    existing_queue = state.get("task_queue", [])
    
    # RESUMPTION LOGIC: If user says "continue", "next", "ok" etc. 
    # and we have a queue, don't re-decompose.
    resumption_keywords = ["continue", "next", "ok", "proceed", "resume", "yes", "go", "go on", "let's go"]
    if existing_queue and any(k == user_msg or user_msg.startswith(k) for k in resumption_keywords):
        return {"task_queue": existing_queue}

    # SELF-HEALING BYPASS: Error feedback from a failed WRITE/DELETE task
    # Skip decomposition and send it directly for immediate script repair
    if "exec_failed:" in user_msg:
        return {"task_queue": [state['user_input']]}

    llm = _get_langchain_llm()
    prompt = f"""
    You are a Task Decomposer for an Enterprise AI. 
    Analyze the following User Input and break it down into a list of atomic, sequential steps.
    
    CRITICAL RULES:
    1. BREAK DOWN the input into ALL distinct actions requested.
    2. If the user asks for multiple things (e.g., "read X and then delete Y"), return them as separate strings in a list.
    3. DO NOT omit any part of the request.
    4. If it's a simple greeting, return it as a single task.
    
    User Input: {state['user_input']}
    
    Return the result as a JSON list of strings.
    Example Input: "Read deneme1.txt then create deneme3.txt then delete deneme2.txt"
    Result: ["Read deneme1.txt on the desktop", "Create deneme3.txt on the desktop", "Delete deneme2.txt from the desktop"]
    
    Return ONLY the JSON list. No other text.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content_raw = response.content
    if isinstance(content_raw, list):
        content_str = content_raw[0].get("text", "") if len(content_raw) > 0 and isinstance(content_raw[0], dict) else str(content_raw[0]) if len(content_raw) > 0 else ""
    else:
        content_str = str(content_raw)
        
    try:
        clean_json = content_str.strip().replace("```json", "").replace("```", "").strip()
        tasks = json.loads(clean_json)
        if not isinstance(tasks, list):
            tasks = [state['user_input']]
        if not tasks:
            tasks = [state['user_input']]
    except:
        tasks = [state['user_input']]
        
    return {"task_queue": tasks}

def pop_next_task_node(state: AgentState):
    """
    Pops the next step from the task_queue and sets it as the current active input for following nodes.
    """
    queue = state.get("task_queue", [])
    if not queue:
        return {"user_input": "", "task_queue": []}
    
    current_step = queue[0]
    remaining = queue[1:]
    
    return {
        "user_input": current_step, 
        "task_queue": remaining
    }
