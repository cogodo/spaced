"""Factory for creating LLM provider instances."""

from typing import Literal

from app.config import settings
from core.llm.base import LLMProvider


def get_llm_provider(model_tier: Literal["default", "fast"] = "default") -> LLMProvider:
    """Get an LLM provider instance based on configuration.

    Args:
        model_tier: The model tier to use.
            - "default": Primary model for complex tasks (Sonnet for Anthropic)
            - "fast": Lighter model for simpler tasks (Haiku for Anthropic)

    Returns:
        An LLMProvider instance configured for the specified tier.

    Raises:
        ValueError: If configuration is invalid or provider not available.
    """
    if settings.use_anthropic:
        from core.llm.anthropic import AnthropicProvider

        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when USE_ANTHROPIC=true")

        if model_tier == "fast":
            model = settings.anthropic_fast_model
        else:
            model = settings.anthropic_model

        return AnthropicProvider(model=model)

    # Fallback to OpenAI (future implementation)
    raise ValueError(
        "OpenAI provider not implemented in abstraction layer. " "Set USE_ANTHROPIC=true or implement OpenAI provider."
    )
