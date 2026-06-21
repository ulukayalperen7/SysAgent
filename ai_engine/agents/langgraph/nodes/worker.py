from langchain_core.messages import HumanMessage
from core.agent_state import AgentState
from core.response_parse import parse_explanation_and_script
from core.executor import ExecutorService
from core.security_guardian import SecurityGuardian
from core.script_policy import (
    format_terminal_proposal,
    propose_deterministic_script,
    validate_command_risk,
)
from .base import _get_langchain_llm

MAX_SAFE_COMMAND_RETRIES = 5

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
    from agents.crewai.crew import SystemDiagnosticsCrew

    crew_instance = SystemDiagnosticsCrew()

    history_str = _compact_history(state.get("messages", []), max_messages=8, max_chars=400)
        
    # Serialize metrics to string to pass to CrewAI prompt safely
    metrics_context = state.get("metrics", {})
    os_name = _target_os_name(state)
    summarized_metrics = (
        f"CPU: {metrics_context.get('cpuUsage', 0)}%, "
        f"RAM: {metrics_context.get('ramUsage', 0)}%, "
        f"Disk: {metrics_context.get('usedDisk', 0)//(1024**3)}GB used."
    )
    target_context = _format_target_context(state)
    
    inputs = {
        "metrics": summarized_metrics,
        "user_prompt": state["user_input"],
        "history": history_str,
        "os_type": os_name,
        "target_context": target_context,
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
    os_name = _target_os_name(state)
    intent = state.get("current_intent", "UNKNOWN")

    # Prefer deterministic proposals for common terminal operations. This keeps
    # app/file/media commands stable and avoids unnecessary LLM variability.
    context_messages = _messages_with_screen_context(state)
    deterministic = propose_deterministic_script(
        state["user_input"],
        intent,
        os_name,
        context_messages=context_messages,
    )
    if deterministic:
        return _finalize_script_proposal(state, deterministic.explanation, deterministic.script, os_name, intent)

    llm = _get_langchain_llm()
    
    history_str = _compact_history(state.get("messages", []), max_messages=8, max_chars=400)
    target_context = _format_target_context(state)

    platform_rules = ""
    if "win" in os_name.lower():
        platform_rules = """
    WINDOWS POWERSHELL RULES (critical - follow exactly):
    - ALWAYS use "$env:USERPROFILE" for home.
    - Desktop path: "$env:USERPROFILE\\Desktop"
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
    Target Context: {target_context}
    User Input: {state['user_input']}
    
    Context History:
    {history_str}
    
    You MUST respond in the following EXACT format:
    Explanation: <A very brief description of what you are about to do>
    Script: <The exact command to run in the terminal>
    
    {platform_rules}
    
    AUTONOMOUS PRECISENESS RULES:
    - Prefer simple, minimal, OS-native commands.
    - For app control, generate generic commands based on the app/process name; do not hardcode one app.
    - For media controls on Windows, use a User32 virtual-key PowerShell script for next/previous/play-pause.
    - For file writes/deletes, use -LiteralPath where possible and target user folders such as Desktop/Downloads/Documents.
    - Include only the current step; the LangGraph queue handles future steps.
    - If you are targeting a specific application, ALWAYS prioritize commands that find, focus, and target that application's Window or Process directly.
    - AVOID using ambiguous global hotkeys (like MediaPlayPause or Spacebar) unless you have first ensured the correct window is in focus.
    - If User Input contains EXEC_FAILED, VERIFICATION_FAILED, or VERIFICATION_UNCERTAIN, repair only that same current step and do not repeat the same failed strategy.
    - GENERATE COMMANDS ONLY FOR THE CURRENT "User Input" STEP. Do not include actions from previous or future tasks.
    - If Context History mentions old tasks, ignore them unless User Input explicitly asks for them now.
    - Never combine unrelated operations in one script.
    
    IMPORTANT:
    - Target Context is metadata only. Do not claim remote execution succeeded; Spring Boot controls final execution.
    - NO markdown code fences in the Script value. Raw command only.
    - If no command is needed, you MUST still say 'Script: NONE'.
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
    except Exception:
        explanation = "The language model timed out while generating a script for this request."
        return {"script": "NONE", "explanation": explanation, "messages": [{"role": "ai", "content": explanation}]}
    content_raw = response.content
    if isinstance(content_raw, list):
        content_str = content_raw[0].get("text", "") if len(content_raw) > 0 and isinstance(content_raw[0], dict) else str(content_raw[0]) if len(content_raw) > 0 else ""
    else:
        content_str = str(content_raw)
        
    explanation, script = parse_explanation_and_script(content_str)
    
    if script and script != "NONE":
        return _finalize_script_proposal(state, explanation, script, os_name, intent)

    msg = {"role": "ai", "content": explanation}
    current_explanation = state.get("explanation", "")
    new_explanation = f"{current_explanation}\n{explanation}".strip()
    return {"script": "NONE", "explanation": new_explanation, "messages": [msg]}


def _finalize_script_proposal(state: AgentState, explanation: str, script: str, os_name: str, intent: str):
    """
    Apply security and risk policy to a proposed script before it reaches Angular.

    The script is still only a proposal. Risky execution remains gated by the
    frontend approval button and Spring Boot's ScriptExecutionService.
    """
    is_safe, sec_reason = SecurityGuardian.validate_command(script, os_name)
    if not is_safe:
        block_msg = f"Security Guardian Blocked: {sec_reason}"
        return {
            "explanation": block_msg,
            "script": "NONE",
            "messages": [{"role": "ai", "content": block_msg}]
        }

    risk = validate_command_risk(script, intent, os_name)
    from core.script_policy import ScriptProposal

    proposal = ScriptProposal(
        explanation=explanation,
        script=script,
        risk_level=risk.risk_level,
        rollback=risk.rollback,
    )

    remaining_tasks = state.get("task_queue", [])
    pending_info = ""
    if remaining_tasks:
        pending_info = f"\n\n**(Pending after this step: {len(remaining_tasks)} more tasks)**"

    terminal_explanation = f"{format_terminal_proposal(proposal)}{pending_info}"
    msg = {"role": "ai", "content": terminal_explanation}
    current_explanation = state.get("explanation", "")
    new_explanation = f"{current_explanation}\n{terminal_explanation}".strip()
    return {"script": script, "explanation": new_explanation, "messages": [msg]}


def _format_target_context(state: AgentState) -> str:
    context = state.get("device_context") or {}
    mode = context.get("execution_mode") or "local_backend"
    if mode == "remote_device":
        name = context.get("name") or f"Device #{state.get('target_device_id')}"
        device_type = context.get("type") or "Unknown"
        status = context.get("status") or "unknown"
        base = f"Remote device '{name}' ({device_type}, status={status})."
        screen = _format_screen_context(context.get("screen_context") or {})
        return f"{base} {screen}".strip()
    return "Local backend host."


def _format_screen_context(screen: dict) -> str:
    if not screen:
        return "No recent desktop screen context is available."
    active_window = screen.get("active_window_title") or "unknown window"
    active_process = screen.get("active_process_name") or "unknown process"
    captured_at = screen.get("captured_at") or "unknown time"
    dimensions = ""
    if screen.get("screen_width") and screen.get("screen_height"):
        dimensions = f" Screen size: {screen.get('screen_width')}x{screen.get('screen_height')}."
    has_screenshot = "yes" if screen.get("has_screenshot") else "no"
    summary = screen.get("vision_summary")
    summary_text = f" Vision summary: {summary}" if summary else ""
    return (
        f"Latest desktop context captured at {captured_at}: "
        f"active window='{active_window}', active process='{active_process}', "
        f"screenshot_available={has_screenshot}.{dimensions}{summary_text}"
    )


def _messages_with_screen_context(state: AgentState) -> list[dict]:
    messages = list(state.get("messages", []))
    context = state.get("device_context") or {}
    screen = context.get("screen_context") or {}
    active_process = screen.get("active_process_name")
    if active_process:
        messages.append(
            {
                "role": "system",
                "content": f"Current desktop active application/process named '{active_process}'.",
            }
        )
    active_window = screen.get("active_window_title")
    if active_window:
        messages.append(
            {
                "role": "system",
                "content": f"Current desktop active window title is '{active_window}'.",
            }
        )
    vision_summary = screen.get("vision_summary")
    if vision_summary:
        messages.append(
            {
                "role": "system",
                "content": f"Current desktop screenshot summary: {vision_summary}",
            }
        )
    return messages


def _target_os_name(state: AgentState) -> str:
    context = state.get("device_context") or {}
    device_type = str(context.get("type") or "").upper()
    if device_type == "WINDOWS":
        return "Windows"
    if device_type == "LINUX":
        return "Linux"
    if device_type == "MACOS":
        return "macOS"
    return state.get("os_type", "Unknown OS")

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
        try:
            summary_response = llm.invoke([HumanMessage(content=summary_prompt)])
        except Exception:
            clean_answer = stdout_text or "The command completed successfully."
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
        
        if retry < MAX_SAFE_COMMAND_RETRIES:
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
