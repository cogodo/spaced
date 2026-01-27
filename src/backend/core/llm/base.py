"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Provides a unified interface for making LLM calls across different providers
    (e.g., OpenAI, Anthropic).
    """

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> str:
        """Generate a text completion.

        Args:
            prompt: The user prompt/input.
            system_prompt: Optional system instructions.
            max_tokens: Maximum tokens in the response.
            timeout: Request timeout in seconds.

        Returns:
            The generated text response.

        Raises:
            Exception: If the API call fails after retries.
        """
        pass

    @abstractmethod
    async def complete_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """Generate a structured JSON completion.

        Args:
            prompt: The user prompt/input with JSON schema instructions.
            response_model: Pydantic model for validating the response.
            system_prompt: Optional system instructions.
            max_tokens: Maximum tokens in the response.
            timeout: Request timeout in seconds.

        Returns:
            Parsed and validated dictionary matching the response model.

        Raises:
            ValueError: If JSON parsing or validation fails after retries.
            Exception: If the API call fails after retries.
        """
        pass
