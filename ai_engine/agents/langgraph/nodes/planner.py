import json
import re
from langchain_core.messages import HumanMessage
from core.agent_state import AgentState
from .base import _get_langchain_llm

CHAT_SHORTCUTS = {"hi", "hello", "hey", "selam", "merhaba", "sa", "slm"}

def decompose_task_node(state: AgentState):
    """
    Analyzes the user input and decomposes it into a list of atomic tasks.
    If the input is simple, it returns a single-item list.
    """
    user_msg = state.get("user_input", "").lower().strip()
    existing_queue = state.get("task_queue", [])
    
    # RESUMPTION LOGIC: If user says "continue", "next", "ok" etc. 
    # and we have a queue, don't re-decompose.
    resumption_keywords = [
        "continue", "next", "ok", "proceed", "resume", "yes", "go", "go on", "let's go",
        "devam", "sonraki", "tamam", "evet", "olur",
    ]
    if existing_queue and any(k == user_msg or user_msg.startswith(k) for k in resumption_keywords):
        return {"task_queue": existing_queue}

    # SELF-HEALING BYPASS: Error or verification feedback from the terminal
    # must stay as one repair prompt for the worker.
    if _is_repair_feedback(user_msg):
        return {"task_queue": [state['user_input']]}

    # Fast path for simple chat and common multi-step terminal commands. This
    # keeps the terminal responsive even when the LLM provider is slow/down.
    if user_msg in CHAT_SHORTCUTS:
        return {"task_queue": [state["user_input"]]}

    deterministic_tasks = _deterministic_decompose(state["user_input"])
    if len(deterministic_tasks) > 1:
        return {"task_queue": deterministic_tasks}
    if _looks_like_single_terminal_task(user_msg):
        return {"task_queue": deterministic_tasks}

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
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
    except Exception:
        return {"task_queue": [state['user_input']]}
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


def _deterministic_decompose(user_input: str) -> list[str]:
    """
    Split obvious sequential commands before asking the LLM.

    Turkish and English connectors are supported because the terminal is often
    used casually: "open editor sonra next song sonra create file".
    """
    parts = re.split(
        r"\s*(?:;|,?\s+\bthen\b\s+|,?\s+\band then\b\s+|,?\s+\bafter that\b\s+|,?\s+\bsonra\b\s+|,?\s+\bsorna\b\s+|,?\s+\bardından\b\s+)\s*",
        user_input,
        flags=re.IGNORECASE,
    )
    tasks = [part.strip(" .") for part in parts if part and part.strip(" .")]
    return tasks if tasks else [user_input]


def _looks_like_single_terminal_task(user_msg: str) -> bool:
    """
    Keep obvious one-step terminal commands away from the LLM decomposer.

    The worker and intent nodes already know how to handle these requests
    deterministically, so asking an external model just adds latency/failure
    points before we even reach the safe script proposal layer.
    """
    normalized = _normalize_for_matching(user_msg)
    markers = (
        "open ", "launch ", "start ", "close ", "kill ", "quit ",
        " ac", "ac ", "kapat", "sonlandir", "sarki",
        "song", "track", "previous", "next", "skip", "play pause",
        "click", "tikla", "type ", "send keys", "write into", "klavyeden yaz",
        "create", "touch", "delete", "remove", "write", "olustur", "sil", "yaz",
        "desktop", "masaustu", ".txt", ".py", ".log",
        "top memory", "process", "network", "connection", "cpu", "ram",
    )
    return any(marker in normalized for marker in markers)


def _is_repair_feedback(user_msg: str) -> bool:
    return (
        "exec_failed:" in user_msg
        or "verification_failed:" in user_msg
        or "verification_uncertain:" in user_msg
    )


def _normalize_for_matching(text: str) -> str:
    """Fold Turkish characters to ASCII for planner fast-path checks."""
    translation = str.maketrans(
        {
            "\u00e7": "c",
            "\u011f": "g",
            "\u0131": "i",
            "\u00f6": "o",
            "\u015f": "s",
            "\u00fc": "u",
            "\u00c7": "c",
            "\u011e": "g",
            "\u0130": "i",
            "\u00d6": "o",
            "\u015e": "s",
            "\u00dc": "u",
        }
    )
    return text.translate(translation).lower()

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
