"""
LLM provider factory.
AccessPilot AI uses Groq as the primary LLM provider.
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
    Creates the Groq LLM client.
    Called once at startup by the singleton.
    """
    from app.engines.llm.groq_provider import GroqProvider
    logger.info("Creating Groq provider", model=settings.groq_model)
    return GroqProvider()


async def get_llm_client() -> LLMClient:
    """
    Returns the singleton LLM client instance.
    Business services should call this to obtain the active provider.
    """
    return await _LLMClientSingleton.get()


def reset_llm_client() -> None:
    """Reset the singleton — used in tests only."""
    _LLMClientSingleton.reset()
