from typing import Dict, Any
from core.agent_state import AgentState
from core.config import settings
from agents.crewai.crew import SystemDiagnosticsCrew
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from core.response_parse import parse_explanation_and_script
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
    You are an intent classifier for a system diagnostic AI.
    Classify the following user input into EXACTLY ONE of these categories:
    - SYSTEM_OPERATION (Queries about OS stats, RAM, CPU, killing processes, system status)
    - CHAT (Basic greetings, casual chat, thanking)
    - UNKNOWN (If it doesn't fit clearly)
    
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
    
    if intent not in ["SYSTEM_OPERATION", "CHAT"]:
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
