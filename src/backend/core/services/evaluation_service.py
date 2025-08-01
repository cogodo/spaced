import json

from openai import AsyncOpenAI

from app.config import settings
from core.models import Question
from core.models.llm_outputs import FSRSScore
from core.monitoring.logger import get_logger

logger = get_logger(__name__)


class EvaluationError(Exception):
    """Custom exception for errors during evaluation."""

    pass


class EvaluationService:
    """
    This service is responsible for evaluating a user's answer against a question.
    """

    def __init__(self, llm_provider: str = "openai"):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def score_answer(self, question: Question, answer: str, after_hint: bool) -> FSRSScore:
        """
        Scores a user's answer using an LLM with FSRS-based scoring criteria.

        Args:
            question: The Question object being answered.
            answer: The user's answer string.
            after_hint: Boolean indicating if the user received a hint.

        Returns:
            An FSRSScore object containing the score and reasoning.

        Raises:
            ValueError: If the LLM call fails or returns invalid data
        """
        logger.info(f"Scoring answer for question: {question.text[:50]}...")

        prompt = self._build_scoring_prompt(question, answer, after_hint)

        try:
            response = await self._call_openai_for_scoring(prompt)
            score_data = self._parse_scoring_response(response)

            # Validate and create FSRSScore object
            fsrs_score = FSRSScore(**score_data)

            logger.info(f"Scored answer: {fsrs_score.score}/5 - {fsrs_score.reasoning[:100]}...")
            return fsrs_score

        except Exception as e:
            error_msg = f"Failed to score answer: {str(e)}. Please try again or contact support if the issue persists."
            logger.error(f"Error scoring answer: {str(e)}")
            raise ValueError(error_msg) from e

    def _build_scoring_prompt(self, question: Question, answer: str, after_hint: bool) -> str:
        """Creates a detailed scoring prompt based on FSRS criteria."""

        hint_context = ""
        if after_hint:
            hint_context = """
IMPORTANT: This answer was provided AFTER the student received a hint or feedback.
This should factor into the scoring - even correct answers should typically receive
lower scores (3-4 range) when given after hints.
"""
        else:
            hint_context = ""

        return f"""You are an expert educational evaluator using the FSRS (Free Spaced Repetition Scheduler) scoring system.

QUESTION CONTEXT:
Topic: {getattr(question, "topic", "General")}
Difficulty: {question.difficulty}/5
Question Type: {question.type}
Question: {question.text}

STUDENT'S ANSWER:
{answer}

{hint_context}

FSRS SCORING CRITERIA (1-5 scale):
• 5 (Excellent): Really good, comprehensive answer. Shows deep understanding. Clear, accurate, well-explained.
• 4 (Good): Correct answer that demonstrates understanding. May be the result of a gentle hint. Solid but not exceptional.
• 3 (Okay): Correct with minor errors, or correct after significant hint. Shows basic understanding but lacks depth.
• 2 (Incorrect, some recall): Student remembers some concepts but applies them incorrectly. Shows partial knowledge.
• 1 (Incorrect): Completely wrong, irrelevant, or demonstrates no understanding of the concept.

SCORING GUIDELINES:
- Focus on conceptual understanding, not just factual correctness
- Consider the depth and clarity of explanation
- Account for the question difficulty level
- If answer was given after hint, cap maximum score at 4
- Be fair but maintain educational standards

Provide your evaluation as a JSON object with exactly these fields:
{{
    "score": <integer 1-5>,
    "reasoning": "<brief explanation of why this score was assigned>"
}}"""

    async def _call_openai_for_scoring(self, prompt: str) -> str:
        """Makes the OpenAI API call for scoring with proper error handling."""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",  # Using cheaper model for testing
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational evaluator. Always respond with valid JSON containing 'score' and 'reasoning' fields.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.2,  # Low temperature for consistent scoring
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty response")

            return content

        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise ValueError(f"Unable to score answer due to AI service error: {str(e)}") from e

    def _parse_scoring_response(self, response: str) -> dict:
        """Parses the LLM response into a structured format."""
        try:
            # Parse JSON response
            data = json.loads(response)

            # Validate required fields exist
            if "score" not in data or "reasoning" not in data:
                raise ValueError("AI response missing required fields (score and reasoning)")

            # Ensure score is valid integer in range
            score = int(data["score"])
            if not (1 <= score <= 5):
                raise ValueError(f"AI returned invalid score {score} (must be 1-5)")

            return {"score": score, "reasoning": str(data["reasoning"])}

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse scoring response: {str(e)}")
            logger.error(f"Response was: {response}")
            raise ValueError(f"AI returned malformed response: {str(e)}") from e
