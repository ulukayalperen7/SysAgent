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

def detect_intent_node(state: AgentState):
    """
    First node in the LangGraph Orchestrator.
    Determines the Intent of the user to route the graph appropriately.
    """
    llm = _get_langchain_llm()
    prompt = f"""
    You are an intent classifier for an Enterprise AI Agent. 
    Classify the incoming user input into EXACTLY ONE of these categories:
    - FILE_SYSTEM_READ (Listing files, viewing text files, searching for files)
    - FILE_SYSTEM_WRITE (Creating, deleting, modifying, moving files or folders) 
    - APP_CONTROL (Opening, closing, managing desktop applications like Spotify, Chrome)
    - DEVOPS_READ (Checking git status, docker ps, reading package.json, reading code)
    - DEVOPS_WRITE (git push, npm install, docker restart)
    - SYSTEM_OPERATION (Queries about OS stats, RAM, CPU, killing OS processes, system status)
    - NETWORK_READ (Ping, port scanning, checking IP)
    - CHAT (Basic greetings, casual chat, no system operation needed)
    - UNKNOWN (If it doesn't clearly fit any above)
    
    User Input: {state['user_input']}
    
    Output ONLY THE EXACT CATEGORY STRING. Do not add any extra text or punctuation.
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
    
    # We append to the message history using the reducer logic
    msg = {"role": "ai", "content": answer}
    
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
            block_msg = f"⚠ GÜVENLİK MUHAFIZI (Security Guardian) TARAFINDAN ENGELLENDİ: İsteğiniz riskli bulundu.\n\nSebep: {sec_reason}"
            return {
                "explanation": block_msg,
                "script": "NONE",
                "messages": [{"role": "ai", "content": block_msg}]
            }
            
    return {"script": script, "explanation": explanation}


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
        answer = f"İşlem Otonom Olarak Tamamlandı (Safe Read Mode). Çıktı:\n```\n{result.get('stdout', '')}\n```"
    else:
        answer = f"İşlem Sırasında Hata Oluştu:\n```\n{result.get('stderr', '')}\n```"
        
    msg = {"role": "ai", "content": answer}
    
    return {
        "explanation": answer,
        "script": "NONE", # We wipe the script so frontend does not ask for execution approval again
        "messages": [msg]
    }

