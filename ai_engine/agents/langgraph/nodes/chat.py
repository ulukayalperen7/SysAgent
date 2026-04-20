from langchain_core.messages import HumanMessage
from core.agent_state import AgentState
from .base import _get_langchain_llm

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
