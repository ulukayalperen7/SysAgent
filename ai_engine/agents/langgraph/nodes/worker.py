from langchain_core.messages import HumanMessage
from core.agent_state import AgentState
from core.response_parse import parse_explanation_and_script
from core.executor import ExecutorService
from core.security_guardian import SecurityGuardian
from agents.crewai.crew import SystemDiagnosticsCrew
from .base import _get_langchain_llm

def _compact_history(messages: list[dict], max_messages: int = 10, max_chars: int = 500) -> str:
    """
    Keep history bounded to avoid context explosion and old-step contamination.
    """
    if not messages:
        return ""

    selected = messages[-max_messages:]
    lines = []
    for m in selected:
        role = str(m.get("role", "unknown")).capitalize()
        content = str(m.get("content", ""))
        if len(content) > max_chars:
            content = content[:max_chars] + "...(truncated)"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)

def run_crewai_diagnostics_node(state: AgentState):
    """
    Terminal node implementing the Facade Pattern.
    Wraps the existing CrewAI architecture, hands over control, and retrieves the expert final report.
    """
    crew_instance = SystemDiagnosticsCrew()

    history_str = _compact_history(state.get("messages", []), max_messages=8, max_chars=400)
        
    # Serialize metrics to string to pass to CrewAI prompt safely
    metrics_context = state.get("metrics", {})
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
    
    history_str = _compact_history(state.get("messages", []), max_messages=8, max_chars=400)

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
    
    AUTONOMOUS PRECISENESS RULES:
    - If you are targeting a specific application (e.g., Spotify, Chrome, Code), ALWAYS prioritize commands that find, focus, and target that application's Window or Process directly.
    - AVOID using ambiguous global hotkeys (like MediaPlayPause or Spacebar) unless you have first ensured the correct window is in focus.
    - If the user had a failure previously, analyze the Context History and do not repeat the same failed strategy.
    - GENERATE COMMANDS ONLY FOR THE CURRENT "User Input" STEP. Do not include actions from previous or future tasks.
    - If Context History mentions old tasks, ignore them unless User Input explicitly asks for them now.
    - Never combine unrelated operations in one script.
    
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
            block_msg = f"Security Guardian Blocked: {sec_reason}"
            return {
                "explanation": block_msg,
                "script": "NONE",
                "messages": [{"role": "ai", "content": block_msg}]
            }
        
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
            return {
                "script": "NONE",
                "messages": [sys_msg],
                "errors": [result.get('stderr', 'Unknown Auto-Correction Error')],
                "retry_count": retry + 1
            }
        else:
            current_explanation = state.get("explanation", "")
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
