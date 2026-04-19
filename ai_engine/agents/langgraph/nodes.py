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
    
    # RESUMPTION LOGIC: If user says "continue", "next", "ok" etc. 
    # and we have a queue, don't re-decompose.
    resumption_keywords = ["continue", "next", "ok", "proceed", "resume", "yes", "go", "go on", "let's go"]
    if existing_queue and any(k == user_msg or user_msg.startswith(k) for k in resumption_keywords):
        return {"task_queue": existing_queue}

    # SELF-HEALING BYPASS: Error feedback from a failed WRITE/DELETE task
    # Skip decomposition and send it directly for immediate script repair
    if user_msg.startswith("exec_failed:"):
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
        content_str = content_raw[0].get("text", "") if len(content_raw) > 0 and isinstance(content_raw[0], dict) else str(content_raw[0]) if len(content_raw) > 0 else ""
    else:
        content_str = str(content_raw)
        
    answer = content_str.strip()
    msg = {"role": "ai", "content": answer}
    
    # For simple chat, synthesis node is overkill - just write result directly
    return {
        "explanation": answer,
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

    platform_rules = ""
    if "win" in os_name.lower():
        platform_rules = """
    WINDOWS POWERSHELL RULES (critical - follow exactly):
    - ALWAYS use "$env:USERPROFILE" for home.
    - Desktop path: "$env:USERPROFILE\Desktop"
    - ALL paths in double quotes.
    - For new files: Use 'New-Item -Path ... -ItemType File' (Avoid -Force unless overwrite requested).
    - For deleting: Use 'Remove-Item -Path ... -Force'.
    - For writing: Use 'Set-Content -Path ... -Value "..." -Force'
    - For reading: Use 'Get-Content -Path "..."'
    - NO markdown code fences. Raw command only.
        """
    else:
        platform_rules = """
    UNIX BASH RULES:
    - ALWAYS use absolute paths or $HOME.
    - Use standard commands: ls, cat, rm, mkdir, touch.
    - Wrap paths in quotes.
        """

    prompt = f"""
    You are a system command generator. Your intent is {intent}.
    Target OS: {os_name}
    User Input: {state['user_input']}
    
    Context History:
    {history_str}
    
    You MUST respond in the following EXACT format:
    Explanation: <A very brief description of what you are about to do>
    Script: <The exact command to run in the terminal>
    
    {platform_rules}
    
    IMPORTANT:
    - NO markdown code fences in the Script value. Raw command only.
    - If no command is needed, you MUST still say 'Script: NONE'.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content_raw = response.content
    if isinstance(content_raw, list):
        content_str = content_raw[0].get("text", "") if len(content_raw) > 0 and isinstance(content_raw[0], dict) else str(content_raw[0]) if len(content_raw) > 0 else ""
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
        
    msg = {"role": "ai", "content": explanation}
    current_explanation = state.get("explanation", "")
    new_explanation = f"{current_explanation}\n{explanation}{pending_info}".strip()
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
    
    if result.get("success"):
        stdout_text = result.get("stdout", "").strip()
        # Use LLM to summarize stdout cleanly instead of dumping raw output
        llm = _get_langchain_llm()
        summary_prompt = f"""The user asked: '{state.get('user_input')}'
The command ran successfully and produced this output:
{stdout_text}

Summarize the result in 1-3 clear sentences for the user. Be direct and factual. No markdown fences."""
        summary_response = llm.invoke([HumanMessage(content=summary_prompt)])
        content_raw = summary_response.content
        if isinstance(content_raw, list):
            clean_answer = content_raw[0].get("text", "") if len(content_raw) > 0 and isinstance(content_raw[0], dict) else str(content_raw[0]) if len(content_raw) > 0 else stdout_text
        else:
            clean_answer = str(content_raw).strip() or stdout_text
        
        current_explanation = state.get("explanation", "")
        new_explanation = f"{current_explanation}\n{clean_answer}".strip()
        msg = {"role": "ai", "content": clean_answer}
        return {
            "explanation": new_explanation,
            "script": "NONE",
            "messages": [msg],
            "retry_count": 0,
            "errors": []
        }
    else:
        retry = state.get("retry_count", 0)
        sys_msg = {"role": "system", "content": f"The script you generated failed with stderr:\n{result.get('stderr', '')}\nPlease generate a corrected script to accomplish the task."}
        
        if retry < 2:
            # Silent retry, feed error back to LLM context
            return {
                "script": "NONE",
                "messages": [sys_msg],
                "errors": [result.get('stderr', 'Unknown Auto-Correction Error')],
                "retry_count": retry + 1
            }
        else:
            # Fatal failure after retries, notify user
            answer = f"{state.get('user_input')} Failed (After Retries):\n```\n{result.get('stderr', '')}\n```"
            new_explanation = f"{current_explanation}\n{answer}".strip()
            msg = {"role": "ai", "content": answer}
            
            return {
                "explanation": new_explanation,
                "script": "NONE",
                "messages": [msg],
                "errors": [],
                "retry_count": 0
            }

def final_synthesis_node(state: AgentState):
    """
    Called when the task queue is empty.
    Reads the accumulated messages (which include stdout from executed commands)
    and provides a final, synthesized answer to the user.
    """
    llm = _get_langchain_llm()
    prompt = """
You are the final response synthesizer for SysAgent Enterprise AI.
Review the conversation and system execution history.
Provide a clear, brief, and helpful final response to the user.
If the user requested data (like reading a file or checking ping), present the information clearly.
If the user only requested actions (like creating/deleting a file) and they succeeded, just say "All requested actions have been completed successfully."
CRITICAL: DO NOT output JSON, raw code blocks, or system logs unless specifically asked. Respond in natural language.
    """
    messages = state.get("messages", []) + [{"role": "system", "content": prompt}]
    
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    lc_messages = []
    for m in messages:
        if m["role"] == "user": lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "system": lc_messages.append(SystemMessage(content=m["content"]))
        elif m["role"] == "ai": lc_messages.append(AIMessage(content=m["content"]))
        
    response = llm.invoke(lc_messages)
    content_raw = response.content
    if isinstance(content_raw, list):
        final_text = content_raw[0].get("text", "") if len(content_raw) > 0 and isinstance(content_raw[0], dict) else str(content_raw[0]) if len(content_raw) > 0 else ""
    else:
        final_text = str(content_raw)
        
    current_explanation = state.get("explanation", "")
    new_explanation = f"{current_explanation}\n\n{final_text}".strip()
    
    return {"explanation": new_explanation}
