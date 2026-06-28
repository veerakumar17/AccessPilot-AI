"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod

from app.engines.llm.models import ExplanationResponse, FixResponse, SimulationResponse


class LLMClient(ABC):
    """
    Abstract interface for LLM providers (Ollama, OpenAI, etc.).
    Business services must depend only on this interface.

    Switching providers requires only changing LLM_PROVIDER in .env.
    """

    @abstractmethod
    async def generate_explanation(self, prompt: str) -> ExplanationResponse:
        """Generate a plain-English explanation for an accessibility violation."""
        ...

    @abstractmethod
    async def generate_fix(self, prompt: str) -> FixResponse:
        """Generate a code fix for an accessibility violation."""
        ...

    @abstractmethod
    async def generate_simulation(self, prompt: str) -> SimulationResponse:
        """Generate a disability simulation description."""
        ...