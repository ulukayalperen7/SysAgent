from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    """
    Centralized configuration for the AI Engine.
    Loads settings from environment variables or .env file.
    """
    # LLM Settings
    # LLM Settings
    llm_provider: str = Field(default="gemini", env="LLM_PROVIDER")
    llm_model: str = Field(default="gemini-2.5-flash", env="LLM_MODEL")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")

    # API Settings
    port: int = Field(default=8001, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")
    debug_mode: bool = Field(default=True, env="DEBUG")

    # Crew: only one concurrent run by default (LLM + shared context); increase via env if needed
    crew_concurrency: int = Field(default=1, ge=1, le=8, env="CREW_CONCURRENCY")

    # LangChain Tracing
    langchain_tracing_v2: str = Field(default="false", env="LANGCHAIN_TRACING_V2")
    langchain_endpoint: str = Field(default="https://api.smith.langchain.com", env="LANGCHAIN_ENDPOINT")
    langchain_api_key: str = Field(default="", env="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="SysAgent", env="LANGCHAIN_PROJECT")

    # DB Settings (Supabase)
    database_url: str = Field(default="", env="DATABASE_URL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

# Instantiate settings globally
settings = Settings()

def get_llm():
    """
    Returns the configured LLM name/instance based on settings.
    For CrewAI, using the model string with provider prefix is often most reliable.
    """
    # Performance & Reliability: Prevent LiteLLM from hanging on network calls for cost maps
    os.environ["LITELLM_OFFLINE"] = "True"
    os.environ["LITELLM_LOCAL_RESOURCES"] = "True"
    
    if settings.llm_provider.lower() == "gemini":
        api_key = settings.google_api_key or settings.gemini_api_key
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is not set.")
        
        # Ensure API keys are in environment for LiteLLM (CrewAI uses LiteLLM internally)
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key
        
        # LiteLLM (CrewAI's engine) uses 'gemini/' prefix to differentiate 
        # Google AI Studio (API Key) from Google Cloud Vertex AI.
        model_name = settings.llm_model
        if not model_name.startswith("gemini/"):
            model_name = f"gemini/{model_name}"
        
        # returning the string allows CrewAI to handle the LiteLLM routing properly
        return model_name
        
    elif settings.llm_provider.lower() == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        return settings.llm_model
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
