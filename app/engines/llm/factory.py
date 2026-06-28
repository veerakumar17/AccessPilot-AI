"""
LLM provider factory.
Switching providers requires only changing LLM_PROVIDER in .env.
"""
from __future__ import annotations

import asyncio

import structlog

from app.config import get_settings
from app.engines.llm.base import LLMClient

logger = structlog.get_logger(__name__)
settings = get_settings()


class _LLMClientSingleton:
    """Thread-safe singleton that holds the active LLM client instance."""
    _instance: LLMClient | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def get(cls) -> LLMClient:
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = create_llm_client()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton — used in tests only."""
        cls._instance = None


def create_llm_client() -> LLMClient:
    """
    Creates the appropriate LLM client based on LLM_PROVIDER setting.
    Called once at startup by the singleton.
    """
    provider = settings.llm_provider.lower().strip()

    if provider == "openai":
        from app.engines.llm.openai_provider import OpenAIProvider
        logger.info("Creating OpenAI provider")
        return OpenAIProvider()

    elif provider == "ollama":
        from app.engines.llm.ollama_provider import OllamaProvider
        logger.info("Creating Ollama provider", base_url=settings.ollama_base_url, model=settings.ollama_model)
        return OllamaProvider()

    elif provider == "gemini":
        from app.engines.llm.gemini_provider import GeminiProvider
        logger.info("Creating Gemini provider", model=settings.gemini_model)
        return GeminiProvider()

    elif provider == "groq":
        from app.engines.llm.groq_provider import GroqProvider
        logger.info("Creating Groq provider", model=settings.groq_model)
        return GroqProvider()

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. "
            f"Expected 'ollama', 'openai', 'gemini', or 'groq'."
        )


async def get_llm_client() -> LLMClient:
    """
    Returns the singleton LLM client instance.
    Business services should call this to obtain the active provider.
    """
    return await _LLMClientSingleton.get()


def reset_llm_client() -> None:
    """Reset the singleton — used in tests only."""
    _LLMClientSingleton.reset()