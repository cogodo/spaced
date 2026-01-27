"""Pytest fixtures and configuration for Spaced backend tests."""

from typing import Any, Dict, Optional, Type

import pytest
from pydantic import BaseModel

from core.llm.base import LLMProvider
from core.models import Question
from core.models.llm_outputs import CombinedStateUpdate, CombinedTurnPayload, NextAction


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing.

    Can be configured to return specific responses or raise exceptions.
    """

    def __init__(
        self,
        complete_response: str = "Mock response",
        structured_response: Optional[Dict[str, Any]] = None,
        raise_on_complete: Optional[Exception] = None,
        raise_on_structured: Optional[Exception] = None,
    ):
        self.complete_response = complete_response
        self.structured_response = structured_response or {}
        self.raise_on_complete = raise_on_complete
        self.raise_on_structured = raise_on_structured
        self.complete_calls: list = []
        self.structured_calls: list = []

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> str:
        self.complete_calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
                "timeout": timeout,
            }
        )
        if self.raise_on_complete:
            raise self.raise_on_complete
        return self.complete_response

    async def complete_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        self.structured_calls.append(
            {
                "prompt": prompt,
                "response_model": response_model,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
                "timeout": timeout,
            }
        )
        if self.raise_on_structured:
            raise self.raise_on_structured
        return self.structured_response


@pytest.fixture
def mock_llm_provider():
    """Factory fixture for creating mock LLM providers."""

    def _create(
        complete_response: str = "Mock response",
        structured_response: Optional[Dict[str, Any]] = None,
        raise_on_complete: Optional[Exception] = None,
        raise_on_structured: Optional[Exception] = None,
    ) -> MockLLMProvider:
        return MockLLMProvider(
            complete_response=complete_response,
            structured_response=structured_response,
            raise_on_complete=raise_on_complete,
            raise_on_structured=raise_on_structured,
        )

    return _create


@pytest.fixture
def valid_combined_response() -> Dict[str, Any]:
    """Valid response for CombinedService."""
    return {
        "user_facing_response": "Great job! You've shown good understanding.",
        "state_update": {
            "score": 4,
            "reasoning": "Student demonstrated solid grasp of the concept.",
            "hint_given": False,
            "misconception": None,
            "next_action": "next_question",
        },
    }


@pytest.fixture
def sample_question() -> Question:
    """Sample question for testing."""
    return Question(
        id="test-question-123",
        topicId="test-topic-456",
        text="What is the capital of France?",
        type="short_answer",
        difficulty=2,
        tags=["geography", "europe"],
        metadata={"generated_by": "test"},
    )


@pytest.fixture
def combined_turn_payload() -> CombinedTurnPayload:
    """Valid CombinedTurnPayload for testing."""
    return CombinedTurnPayload(
        user_facing_response="Good answer! Paris is indeed the capital.",
        state_update=CombinedStateUpdate(
            score=5,
            reasoning="Correct answer with confidence.",
            hint_given=False,
            misconception=None,
            next_action=NextAction.MOVE_TO_NEXT_QUESTION,
        ),
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests requiring API keys")
