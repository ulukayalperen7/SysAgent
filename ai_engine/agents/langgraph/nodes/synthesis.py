from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from core.agent_state import AgentState
from .base import _get_langchain_llm

def _bounded_messages(messages: list[dict], max_messages: int = 12, max_chars: int = 500) -> list[dict]:
    trimmed = messages[-max_messages:] if messages else []
    result = []
    for m in trimmed:
        content = str(m.get("content", ""))
        if len(content) > max_chars:
            content = content[:max_chars] + "...(truncated)"
        result.append({"role": m.get("role", "system"), "content": content})
    return result

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
    messages = _bounded_messages(state.get("messages", []), max_messages=12, max_chars=500) + [{"role": "system", "content": prompt}]
    
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
