"""
Backward-compatible re-export of the LLM client interface.
New code should import from app.engines.llm instead.
"""
from app.core.exceptions import OpenAIException
from app.engines.llm import (
    LLMClient,
    ExplanationResponse,
    FixResponse,
    SimulationResponse,
    get_llm_client,
    create_llm_client,
    reset_llm_client,
)

__all__ = [
    "LLMClient",
    "ExplanationResponse",
    "FixResponse",
    "SimulationResponse",
    "get_llm_client",
    "create_llm_client",
    "reset_llm_client",
    "OpenAIException",
    "OpenAIClient",
    "get_openai_client",
]

# Maintain backward-compatible alias for existing imports
get_openai_client = get_llm_client
OpenAIClient = LLMClient
