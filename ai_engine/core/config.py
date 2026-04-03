from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    """
    Centralized configuration for the AI Engine.
    Loads settings from environment variables or .env file.
    """
    # LLM Settings
    llm_provider: str = Field(default="gemini", env="LLM_PROVIDER")
    llm_model: str = Field(default="gemini-2.0-flash", env="LLM_MODEL")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")

    # API Settings
    port: int = Field(default=8001, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")
    debug_mode: bool = Field(default=True, env="DEBUG")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate settings globally
settings = Settings()

def get_llm():
    """
    Returns the configured LLM instance based on settings.
    Defaulting to Google Gemini as requested.
    """
    if settings.llm_provider.lower() == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is not set in the environment.")
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=0.3
        )
    elif settings.llm_provider.lower() == "openai":
        from langchain_openai import ChatOpenAI
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set in the environment.")
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=0.3
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
