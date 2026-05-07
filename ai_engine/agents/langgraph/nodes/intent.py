from langchain_core.messages import HumanMessage
from core.agent_state import AgentState
from .base import _get_langchain_llm

CHAT_SHORTCUTS = {"hi", "hello", "hey", "selam", "merhaba", "sa", "slm", "thanks", "thank you"}

def detect_intent_node(state: AgentState):
    """
    Determines the Intent of the current active input.
    """
    current_input = state.get("user_input")

    deterministic_intent = _detect_intent_deterministic(current_input or "")
    if deterministic_intent:
        return {"current_intent": deterministic_intent}

    llm = _get_langchain_llm()
    
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
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
    except Exception:
        return {"current_intent": "UNKNOWN"}
    
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


def _detect_intent_deterministic(user_input: str) -> str | None:
    """Classify common terminal intents without waiting for the LLM."""
    lower = _normalize_for_matching(user_input).strip()
    if lower in CHAT_SHORTCUTS:
        return "CHAT"
    if "exec_failed:" in lower:
        return "UNKNOWN"

    write_terms = ("create", "touch", "delete", "remove", "write", "set content", "move", "rename", "olustur", "sil", "yaz")
    app_terms = (
        "open ", "launch ", "start ", "close ", "kill ", "quit ",
        "next song", "next track", "previous song", "play pause",
        " ac", "ac ", "kapat", "sonlandir", "sarki", "calistir", "baslat",
    )
    devops_write_terms = ("install", "uninstall", "npm install", "pip install", "docker restart", "git push", "winget", "yukle", "kur", "kaldir")
    fs_read_terms = ("list files", "show files", "read file", "show file", "list directory", "downloads", "desktop", "documents", ".txt", ".log")
    network_terms = ("network", "connections", "ports", "ping", "dns", "socket")
    system_terms = ("cpu", "ram", "memory", "process", "processes", "slow", "suspicious", "system", "metrics")

    if any(term in lower for term in devops_write_terms):
        return "DEVOPS_WRITE"
    if any(term in lower for term in write_terms):
        return "FILE_SYSTEM_WRITE"
    if any(term in lower for term in app_terms):
        return "APP_CONTROL"
    if any(term in lower for term in network_terms):
        return "NETWORK_READ"
    if any(term in lower for term in fs_read_terms):
        return "FILE_SYSTEM_READ"
    if any(term in lower for term in system_terms):
        return "SYSTEM_OPERATION"

    return None


def _normalize_for_matching(text: str) -> str:
    """Fold Turkish characters to ASCII so casual terminal text routes reliably."""
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
