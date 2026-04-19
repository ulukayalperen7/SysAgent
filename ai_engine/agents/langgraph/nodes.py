from typing import Dict, Any
from core.agent_state import AgentState
from core.config import settings
from agents.crewai.crew import SystemDiagnosticsCrew
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from core.response_parse import parse_explanation_and_script
from core.executor import ExecutorService
from core.security_guardian import SecurityGuardian
import os
import json

def _get_langchain_llm():
    """
    Returns a proper LangChain LLM instance for use in LangGraph nodes.
    NOTE: get_llm() in config.py returns a string for CrewAI/LiteLLM.
    LangGraph nodes need a real LangChain ChatModel with .invoke() support.
    """
    api_key = settings.google_api_key or settings.gemini_api_key
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is not set.")
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=api_key,
        temperature=0
    )

def decompose_task_node(state: AgentState):
    """
    Analyzes the user input and decomposes it into a list of atomic tasks.
    If the input is simple, it returns a single-item list.
    """
    user_msg = state.get("user_input", "").lower().strip()
    existing_queue = state.get("task_queue", [])
    
    # RESUMPTION LOGIC: If user says "devam", "continue", "donner", "ok" etc. 
    # and we have a queue, don't re-decompose.
    resumption_keywords = ["devam", "devam et", "continue", "next", "ok", "tamam", "hadi", "sıradaki"]
    if existing_queue and any(k == user_msg or user_msg.startswith(k) for k in resumption_keywords):
        # We keep the existing queue as is.
        # But we need to return something to signal "no change" to the reducer.
        # Actually, returning an empty dict or just the existing queue is fine.
        return {"task_queue": existing_queue}

    llm = _get_langchain_llm()
    prompt = f"""
    You are a Task Decomposer for an Enterprise AI. 
    Analyze the following User Input and break it down into a list of atomic, sequential steps.
    
    CRITICAL RULES:
    1. If the input is a simple greeting (e.g., 'hi', 'hello', 'how are you'), return it as a single task. DO NOT split it.
    2. If the input is a single command or question, return it as a single task.
    3. ONLY split if the user uses conjunctions like 'and then', 'also', 'after that' or sequential logic.
    
    User Input: {state['user_input']}
    
    Return the result as a JSON list of strings.
    Example Input: "Create a file named logs.txt and then list the directory"
    Result: ["Create a file named logs.txt", "List the directory contents"]
    
    Return ONLY the JSON list. No other text.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content_raw = response.content
    if isinstance(content_raw, list):
        content_str = content_raw[0].get("text", "") if isinstance(content_raw[0], dict) else str(content_raw[0])
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
        content_str = content_raw[0].get("text", "") if isinstance(content_raw[0], dict) else str(content_raw[0])
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


def direct_chat_node(state: AgentState):
    """
    Terminal node for purely conversational intents.
    Bypasses the heavy CrewAI operations for fast, cheap responses.
    """
    llm = _get_langchain_llm()
    prompt = f"""
    You are a friendly AI assistant called SysAgent.
    Respond nicely and concisely to the user's casual chat.
    User Input: {state['user_input']}
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    content_raw = response.content
    if isinstance(content_raw, list):
        content_str = content_raw[0].get("text", "") if isinstance(content_raw[0], dict) else str(content_raw[0])
    else:
        content_str = str(content_raw)
        
    answer = content_str.strip()
    
    current_explanation = state.get("explanation", "")
    new_explanation = f"{current_explanation}\n{answer}".strip()
    
    msg = {"role": "ai", "content": answer}
    
    return {
        "explanation": new_explanation,
        "script": "NONE",
        "messages": [msg]
    }


def run_crewai_diagnostics_node(state: AgentState):
    """
    Terminal node implementing the Facade Pattern.
    Wraps the existing CrewAI architecture, hands over control, and retrieves the expert final report.
    """
    crew_instance = SystemDiagnosticsCrew()

    history_str = ""
    for m in state.get("messages", []):
        history_str += f"{m['role'].capitalize()}: {m['content']}\n"
        
    # Serialize metrics to string to pass to CrewAI prompt safely
    metrics_context = state.get("metrics", {})
    # Provide a simple summarized string representation
    summarized_metrics = (
        f"CPU: {metrics_context.get('cpuUsage', 0)}%, "
        f"RAM: {metrics_context.get('ramUsage', 0)}%, "
        f"Disk: {metrics_context.get('usedDisk', 0)//(1024**3)}GB used."
    )
    
    inputs = {
        "metrics": summarized_metrics,
        "user_prompt": state["user_input"],
        "history": history_str,
        "os_type": state.get("os_type", "Unknown OS")
    }
    
    # Run kickoff
    raw_result = str(crew_instance.crew().kickoff(inputs=inputs))
    
    explanation, script = parse_explanation_and_script(raw_result)
    
    msg = {"role": "ai", "content": explanation}
    
    return {
        "explanation": explanation,
        "script": script,
        "messages": [msg]
    }


def generate_action_script_node(state: AgentState):
    """
    Generates OS-specific scripts for actionable intents and runs them through SecurityGuardian.
    """
    llm = _get_langchain_llm()
    os_name = state.get("os_type", "Unknown OS")
    intent = state.get("current_intent", "UNKNOWN")
    
    history_str = ""
    for m in state.get("messages", []):
        history_str += f"{m['role'].capitalize()}: {m['content']}\n"

    prompt = f"""
    You are a system command generator. Your intent is {intent}.
    Target OS: {os_name}
    User Input: {state['user_input']}
    
    Context History:
    {history_str}
    
    You MUST respond in the following EXACT format:
    Explanation: <A very brief description of what you are about to do>
    Script: <The exact command to run in the terminal>
    
    IMPORTANT: 
    - Use only standard markdown blocks (```bash or ```powershell) for the Script part if needed, but the 'Script:' keyword must be present.
    - If no command is needed, you MUST still say 'Script: NONE'.
    - Ensure the command is correct for {os_name}.
    - Resolve relative paths or file references using the Context History above.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content_raw = response.content
    if isinstance(content_raw, list):
        content_str = content_raw[0].get("text", "") if isinstance(content_raw[0], dict) else str(content_raw[0])
    else:
        content_str = str(content_raw)
        
    explanation, script = parse_explanation_and_script(content_str)
    
    if script and script != "NONE":
        is_safe, sec_reason = SecurityGuardian.validate_command(script, os_name)
        if not is_safe:
            # BLOCKED! Return warning directly to user.
            block_msg = f"Security Guardian Blocked: {sec_reason}"
            return {
                "explanation": block_msg,
                "script": "NONE",
                "messages": [{"role": "ai", "content": block_msg}]
            }
        
        step_exp = explanation
    else:
        step_exp = explanation
        
    # Check if there are more tasks pending in the queue
    remaining_tasks = state.get("task_queue", [])
    pending_info = ""
    if remaining_tasks:
        pending_info = f"\n\n**(Pending after this step: {len(remaining_tasks)} more tasks)**"
        
    current_explanation = state.get("explanation", "")
    new_explanation = f"{current_explanation}\n{explanation}{pending_info}".strip()
    
    msg = {"role": "ai", "content": explanation}
    return {"script": script, "explanation": new_explanation, "messages": [msg]}


def execute_safe_action_node(state: AgentState):
    """
    Autonomous executor for completely safe READ intents. 
    Allows AI to run OS commands instantly without bothering user for manual UI approval.
    """
    script = state.get("script", "NONE")
    
    if script == "NONE":
        return state
        
    result = ExecutorService.execute_safe_command(script)
    
    current_explanation = state.get("explanation", "")
    if result.get("success"):
        answer = f"{state.get('user_input')} Result:\n```\n{result.get('stdout', '')}\n```"
    else:
        answer = f"{state.get('user_input')} Error:\n```\n{result.get('stderr', '')}\n```"
        
    new_explanation = f"{current_explanation}\n{answer}"
    msg = {"role": "ai", "content": answer}
    
    return {
        "explanation": new_explanation.strip(),
        "script": "NONE", 
        "messages": [msg]
    }


