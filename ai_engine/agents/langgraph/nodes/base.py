from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import settings

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
