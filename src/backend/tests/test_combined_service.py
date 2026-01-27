"""Unit tests for CombinedService."""

from unittest.mock import patch

import pytest

from core.models import Question
from core.models.llm_outputs import NextAction
from core.services.combined_service import CombinedService, CombinedServiceError


class TestCombinedService:
    """Tests for CombinedService."""

    @pytest.fixture
    def sample_question(self) -> Question:
        """Create a sample question for testing."""
        return Question(
            id="test-123",
            topicId="topic-456",
            text="What is photosynthesis?",
            type="short_answer",
            difficulty=3,
            tags=["biology", "plants"],
            metadata={"generated_by": "test"},
        )

    @pytest.fixture
    def valid_response(self):
        """Valid structured response from LLM."""
        return {
            "user_facing_response": "Great answer! Photosynthesis is indeed the process by which plants convert light to energy.",
            "state_update": {
                "score": 4,
                "reasoning": "Student showed good understanding of the basic concept.",
                "hint_given": False,
                "misconception": None,
                "next_action": "next_question",
            },
        }

    @pytest.mark.asyncio
    async def test_evaluate_turn_returns_valid_payload(self, sample_question, valid_response, mock_llm_provider):
        """Test that evaluate_turn returns a valid payload structure."""
        mock_provider = mock_llm_provider(structured_response=valid_response)

        with patch("core.services.combined_service.get_llm_provider", return_value=mock_provider):
            service = CombinedService()
            result = await service.evaluate_turn(
                question=sample_question,
                answer="Human: Photosynthesis is when plants use sunlight to make food.",
                after_hint=False,
            )

        assert "user_facing_response" in result
        assert "state_update" in result
        assert result["state_update"]["score"] == 4
        assert result["state_update"]["next_action"] == NextAction.MOVE_TO_NEXT_QUESTION

    @pytest.mark.asyncio
    async def test_score_within_1_to_5_range(self, sample_question, mock_llm_provider):
        """Test that scores are validated to be within 1-5 range."""
        for expected_score in [1, 2, 3, 4, 5]:
            response = {
                "user_facing_response": "Test response",
                "state_update": {
                    "score": expected_score,
                    "reasoning": "Test reasoning",
                    "hint_given": False,
                    "misconception": None,
                    "next_action": "next_question",
                },
            }
            mock_provider = mock_llm_provider(structured_response=response)

            with patch("core.services.combined_service.get_llm_provider", return_value=mock_provider):
                service = CombinedService()
                result = await service.evaluate_turn(
                    question=sample_question,
                    answer="Test answer",
                    after_hint=False,
                )

            assert result["state_update"]["score"] == expected_score
            assert 1 <= result["state_update"]["score"] <= 5

    @pytest.mark.asyncio
    async def test_next_action_next_question(self, sample_question, mock_llm_provider):
        """Test next_action=next_question is handled correctly."""
        response = {
            "user_facing_response": "Correct!",
            "state_update": {
                "score": 5,
                "reasoning": "Perfect answer",
                "hint_given": False,
                "misconception": None,
                "next_action": "next_question",
            },
        }
        mock_provider = mock_llm_provider(structured_response=response)

        with patch("core.services.combined_service.get_llm_provider", return_value=mock_provider):
            service = CombinedService()
            result = await service.evaluate_turn(
                question=sample_question,
                answer="Perfect answer",
                after_hint=False,
            )

        assert result["state_update"]["next_action"] == NextAction.MOVE_TO_NEXT_QUESTION

    @pytest.mark.asyncio
    async def test_next_action_clarification(self, sample_question, mock_llm_provider):
        """Test next_action=clarification is handled correctly."""
        response = {
            "user_facing_response": "Can you tell me more about chlorophyll?",
            "state_update": {
                "score": 3,
                "reasoning": "Partial answer, needs more detail",
                "hint_given": True,
                "misconception": None,
                "next_action": "clarification",
            },
        }
        mock_provider = mock_llm_provider(structured_response=response)

        with patch("core.services.combined_service.get_llm_provider", return_value=mock_provider):
            service = CombinedService()
            result = await service.evaluate_turn(
                question=sample_question,
                answer="Something about green stuff",
                after_hint=False,
            )

        assert result["state_update"]["next_action"] == NextAction.AWAIT_CLARIFICATION
        assert result["state_update"]["hint_given"] is True

    @pytest.mark.asyncio
    async def test_next_action_end_chat(self, sample_question, mock_llm_provider):
        """Test next_action=end_chat is handled correctly."""
        response = {
            "user_facing_response": "Thanks for the session!",
            "state_update": {
                "score": 4,
                "reasoning": "Session complete",
                "hint_given": False,
                "misconception": None,
                "next_action": "end_chat",
            },
        }
        mock_provider = mock_llm_provider(structured_response=response)

        with patch("core.services.combined_service.get_llm_provider", return_value=mock_provider):
            service = CombinedService()
            result = await service.evaluate_turn(
                question=sample_question,
                answer="I want to end",
                after_hint=False,
            )

        assert result["state_update"]["next_action"] == NextAction.END_CHAT

    @pytest.mark.asyncio
    async def test_misconception_captured(self, sample_question, mock_llm_provider):
        """Test that misconceptions are properly captured."""
        response = {
            "user_facing_response": "Not quite - plants don't breathe like animals.",
            "state_update": {
                "score": 2,
                "reasoning": "Confused photosynthesis with respiration",
                "hint_given": True,
                "misconception": "Student confused photosynthesis with cellular respiration",
                "next_action": "clarification",
            },
        }
        mock_provider = mock_llm_provider(structured_response=response)

        with patch("core.services.combined_service.get_llm_provider", return_value=mock_provider):
            service = CombinedService()
            result = await service.evaluate_turn(
                question=sample_question,
                answer="Plants breathe in CO2",
                after_hint=False,
            )

        assert result["state_update"]["misconception"] == "Student confused photosynthesis with cellular respiration"

    @pytest.mark.asyncio
    async def test_raises_combined_service_error_on_failure(self, sample_question, mock_llm_provider):
        """Test that CombinedServiceError is raised on LLM failure."""
        mock_provider = mock_llm_provider(raise_on_structured=ValueError("LLM call failed"))

        with patch("core.services.combined_service.get_llm_provider", return_value=mock_provider):
            service = CombinedService()
            with pytest.raises(CombinedServiceError):
                await service.evaluate_turn(
                    question=sample_question,
                    answer="Test answer",
                    after_hint=False,
                )

    @pytest.mark.asyncio
    async def test_prompt_includes_question_details(self, sample_question, mock_llm_provider):
        """Test that the prompt includes question details."""
        mock_provider = mock_llm_provider(
            structured_response={
                "user_facing_response": "Test",
                "state_update": {
                    "score": 3,
                    "reasoning": "Test",
                    "hint_given": False,
                    "misconception": None,
                    "next_action": "next_question",
                },
            }
        )

        with patch("core.services.combined_service.get_llm_provider", return_value=mock_provider):
            service = CombinedService()
            await service.evaluate_turn(
                question=sample_question,
                answer="Test answer",
                after_hint=False,
            )

        # Check that the prompt was called with question details
        assert len(mock_provider.structured_calls) == 1
        call = mock_provider.structured_calls[0]
        prompt = call["prompt"]

        assert sample_question.text in prompt
        assert str(sample_question.difficulty) in prompt
        assert sample_question.type in prompt


class TestCombinedServiceParsing:
    """Tests for CombinedService response parsing."""

    @pytest.fixture
    def service_with_mock(self, mock_llm_provider):
        """Create a service with a mock provider."""

        def _create(response):
            mock_provider = mock_llm_provider(structured_response=response)
            with patch("core.services.combined_service.get_llm_provider", return_value=mock_provider):
                return CombinedService()

        return _create

    def test_parse_response_strips_whitespace(self):
        """Test that user_facing_response whitespace is stripped."""
        service = CombinedService.__new__(CombinedService)
        data = {
            "user_facing_response": "  Good answer!  \n",
            "state_update": {
                "score": 4,
                "reasoning": "Test",
                "hint_given": False,
                "misconception": None,
                "next_action": "next_question",
            },
        }

        result = service._parse_response(data)
        assert result["user_facing_response"] == "Good answer!"

    def test_parse_response_validates_next_action(self):
        """Test that invalid next_action raises ValueError."""
        service = CombinedService.__new__(CombinedService)
        data = {
            "user_facing_response": "Test",
            "state_update": {
                "score": 4,
                "reasoning": "Test",
                "hint_given": False,
                "misconception": None,
                "next_action": "invalid_action",
            },
        }

        with pytest.raises(ValueError, match="Invalid next_action"):
            service._parse_response(data)
