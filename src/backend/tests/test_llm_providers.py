"""Unit tests for LLM provider abstraction layer."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.llm.anthropic import AnthropicProvider
from core.llm.factory import get_llm_provider
from core.models.llm_outputs import CombinedTurnPayload


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client."""
        mock_client = MagicMock()
        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock()
        return mock_client

    @pytest.mark.asyncio
    async def test_complete_returns_text(self, mock_anthropic_client):
        """Test that complete() returns text from Anthropic response."""
        # Setup mock response
        mock_text_block = MagicMock()
        mock_text_block.text = "This is a test response"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        mock_anthropic_client.messages.create.return_value = mock_response

        with patch("core.llm.anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
            with patch("core.llm.anthropic.settings") as mock_settings:
                mock_settings.anthropic_api_key = "test-key"
                mock_settings.anthropic_max_retries = 2
                mock_settings.anthropic_request_timeout_seconds = 30

                provider = AnthropicProvider(model="claude-sonnet-4-20250514")
                provider.client = mock_anthropic_client

                result = await provider.complete(
                    prompt="Hello, how are you?",
                    system_prompt="You are a helpful assistant.",
                )

        assert result == "This is a test response"
        mock_anthropic_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_retries_on_failure(self, mock_anthropic_client):
        """Test that complete() retries on transient failures."""
        # First call fails, second succeeds
        mock_text_block = MagicMock()
        mock_text_block.text = "Success after retry"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        mock_anthropic_client.messages.create.side_effect = [
            Exception("Transient error"),
            mock_response,
        ]

        with patch("core.llm.anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
            with patch("core.llm.anthropic.settings") as mock_settings:
                mock_settings.anthropic_api_key = "test-key"
                mock_settings.anthropic_max_retries = 2
                mock_settings.anthropic_request_timeout_seconds = 30

                provider = AnthropicProvider(model="claude-sonnet-4-20250514")
                provider.client = mock_anthropic_client

                result = await provider.complete(prompt="Test prompt")

        assert result == "Success after retry"
        assert mock_anthropic_client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_structured_parses_valid_json(self, mock_anthropic_client):
        """Test that complete_structured() parses valid JSON responses."""
        valid_json = {
            "user_facing_response": "Good job!",
            "state_update": {
                "score": 4,
                "reasoning": "Correct answer",
                "hint_given": False,
                "misconception": None,
                "next_action": "next_question",
            },
        }

        mock_text_block = MagicMock()
        mock_text_block.text = json.dumps(valid_json)

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        mock_anthropic_client.messages.create.return_value = mock_response

        with patch("core.llm.anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
            with patch("core.llm.anthropic.settings") as mock_settings:
                mock_settings.anthropic_api_key = "test-key"
                mock_settings.anthropic_max_retries = 2
                mock_settings.anthropic_request_timeout_seconds = 30

                provider = AnthropicProvider(model="claude-sonnet-4-20250514")
                provider.client = mock_anthropic_client

                result = await provider.complete_structured(
                    prompt="Evaluate this answer",
                    response_model=CombinedTurnPayload,
                )

        assert result["user_facing_response"] == "Good job!"
        assert result["state_update"]["score"] == 4

    @pytest.mark.asyncio
    async def test_structured_extracts_json_from_prose(self, mock_anthropic_client):
        """Test that complete_structured() can extract JSON from prose response."""
        # Response with prose before and after JSON
        response_with_prose = """Here's my analysis:
{
    "user_facing_response": "Nice work!",
    "state_update": {
        "score": 5,
        "reasoning": "Perfect answer",
        "hint_given": false,
        "misconception": null,
        "next_action": "next_question"
    }
}
Let me know if you need anything else."""

        mock_text_block = MagicMock()
        mock_text_block.text = response_with_prose

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        mock_anthropic_client.messages.create.return_value = mock_response

        with patch("core.llm.anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
            with patch("core.llm.anthropic.settings") as mock_settings:
                mock_settings.anthropic_api_key = "test-key"
                mock_settings.anthropic_max_retries = 2
                mock_settings.anthropic_request_timeout_seconds = 30

                provider = AnthropicProvider(model="claude-sonnet-4-20250514")
                provider.client = mock_anthropic_client

                result = await provider.complete_structured(
                    prompt="Evaluate this answer",
                    response_model=CombinedTurnPayload,
                )

        assert result["user_facing_response"] == "Nice work!"
        assert result["state_update"]["score"] == 5

    @pytest.mark.asyncio
    async def test_structured_handles_markdown_code_fence(self, mock_anthropic_client):
        """Test that complete_structured() handles JSON in markdown code fences."""
        response_with_fence = """```json
{
    "user_facing_response": "Excellent!",
    "state_update": {
        "score": 5,
        "reasoning": "Great explanation",
        "hint_given": false,
        "misconception": null,
        "next_action": "next_question"
    }
}
```"""

        mock_text_block = MagicMock()
        mock_text_block.text = response_with_fence

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        mock_anthropic_client.messages.create.return_value = mock_response

        with patch("core.llm.anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
            with patch("core.llm.anthropic.settings") as mock_settings:
                mock_settings.anthropic_api_key = "test-key"
                mock_settings.anthropic_max_retries = 2
                mock_settings.anthropic_request_timeout_seconds = 30

                provider = AnthropicProvider(model="claude-sonnet-4-20250514")
                provider.client = mock_anthropic_client

                result = await provider.complete_structured(
                    prompt="Evaluate this answer",
                    response_model=CombinedTurnPayload,
                )

        assert result["user_facing_response"] == "Excellent!"

    @pytest.mark.asyncio
    async def test_structured_retries_on_parse_failure(self, mock_anthropic_client):
        """Test that complete_structured() retries when JSON parsing fails."""
        # First response is invalid, second is valid
        invalid_response = MagicMock()
        invalid_response.text = "This is not valid JSON"

        valid_json = {
            "user_facing_response": "Correct!",
            "state_update": {
                "score": 4,
                "reasoning": "Good answer",
                "hint_given": False,
                "misconception": None,
                "next_action": "next_question",
            },
        }
        valid_response = MagicMock()
        valid_response.text = json.dumps(valid_json)

        mock_response_1 = MagicMock()
        mock_response_1.content = [invalid_response]

        mock_response_2 = MagicMock()
        mock_response_2.content = [valid_response]

        mock_anthropic_client.messages.create.side_effect = [
            mock_response_1,
            mock_response_2,
        ]

        with patch("core.llm.anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
            with patch("core.llm.anthropic.settings") as mock_settings:
                mock_settings.anthropic_api_key = "test-key"
                mock_settings.anthropic_max_retries = 2
                mock_settings.anthropic_request_timeout_seconds = 30

                provider = AnthropicProvider(model="claude-sonnet-4-20250514")
                provider.client = mock_anthropic_client

                result = await provider.complete_structured(
                    prompt="Evaluate this answer",
                    response_model=CombinedTurnPayload,
                )

        assert result["user_facing_response"] == "Correct!"
        assert mock_anthropic_client.messages.create.call_count == 2


class TestLLMFactory:
    """Tests for the LLM provider factory."""

    def test_get_provider_anthropic_default(self):
        """Test getting Anthropic provider with default tier."""
        with patch("core.llm.factory.settings") as mock_settings:
            mock_settings.use_anthropic = True
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.anthropic_model = "claude-sonnet-4-20250514"
            mock_settings.anthropic_fast_model = "claude-3-5-haiku-20241022"

            with patch("core.llm.anthropic.AsyncAnthropic"):
                with patch("core.llm.anthropic.settings", mock_settings):
                    provider = get_llm_provider("default")

            assert isinstance(provider, AnthropicProvider)
            assert provider.model == "claude-sonnet-4-20250514"

    def test_get_provider_anthropic_fast(self):
        """Test getting Anthropic provider with fast tier."""
        with patch("core.llm.factory.settings") as mock_settings:
            mock_settings.use_anthropic = True
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.anthropic_model = "claude-sonnet-4-20250514"
            mock_settings.anthropic_fast_model = "claude-3-5-haiku-20241022"

            with patch("core.llm.anthropic.AsyncAnthropic"):
                with patch("core.llm.anthropic.settings", mock_settings):
                    provider = get_llm_provider("fast")

            assert isinstance(provider, AnthropicProvider)
            assert provider.model == "claude-3-5-haiku-20241022"

    def test_get_provider_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        with patch("core.llm.factory.settings") as mock_settings:
            mock_settings.use_anthropic = True
            mock_settings.anthropic_api_key = None

            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
                get_llm_provider("default")


class TestJSONExtraction:
    """Tests for JSON extraction edge cases."""

    @pytest.fixture
    def provider(self):
        """Create a provider for testing JSON extraction."""
        with patch("core.llm.anthropic.AsyncAnthropic"):
            with patch("core.llm.anthropic.settings") as mock_settings:
                mock_settings.anthropic_api_key = "test-key"
                mock_settings.anthropic_max_retries = 2
                return AnthropicProvider(model="test-model")

    def test_extract_json_direct_parse(self, provider):
        """Test direct JSON parsing."""
        text = '{"key": "value"}'
        result = provider._extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_with_whitespace(self, provider):
        """Test JSON parsing with surrounding whitespace."""
        text = '   \n  {"key": "value"}  \n   '
        result = provider._extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_code_fence(self, provider):
        """Test JSON extraction from code fence."""
        text = '```json\n{"key": "value"}\n```'
        result = provider._extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_prose_before(self, provider):
        """Test JSON extraction with prose before."""
        text = 'Here is the result:\n{"key": "value"}'
        result = provider._extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_prose_after(self, provider):
        """Test JSON extraction with prose after."""
        text = '{"key": "value"}\nThat\'s all.'
        result = provider._extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_nested(self, provider):
        """Test JSON extraction with nested objects."""
        text = '{"outer": {"inner": "value"}}'
        result = provider._extract_json(text)
        assert result == {"outer": {"inner": "value"}}

    def test_extract_json_invalid_raises(self, provider):
        """Test that invalid JSON raises JSONDecodeError."""
        text = "This is not JSON at all"
        with pytest.raises(json.JSONDecodeError):
            provider._extract_json(text)
