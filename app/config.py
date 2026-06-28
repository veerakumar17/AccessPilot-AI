from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "AccessPilot AI"
    app_env: str = "development"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "change-this-secret"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/accesspilot"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # LLM Provider selection: "ollama" (development) or "openai" (production)
    llm_provider: str = "ollama"

    # OpenAI (used when llm_provider = "openai")
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 2048
    openai_max_retries: int = 3
    openai_request_timeout: int = 60

    # Ollama (used when llm_provider = "ollama")
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_request_timeout: int = 120

    # Gemini (used when llm_provider = "gemini")
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_max_tokens: int = 2048

    # Groq (used when llm_provider = "groq")
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_tokens: int = 2048
    groq_max_retries: int = 3
    groq_request_timeout: int = 60

    # Crawler
    crawler_max_pages: int = 20
    crawler_timeout_seconds: int = 30
    crawler_headless: bool = True

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Logging
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
