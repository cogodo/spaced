"""LLM provider abstraction layer for Spaced backend."""

from core.llm.base import LLMProvider
from core.llm.factory import get_llm_provider

__all__ = ["LLMProvider", "get_llm_provider"]
