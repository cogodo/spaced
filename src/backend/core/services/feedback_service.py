import json

from openai import AsyncOpenAI

from app.config import settings
from core.models import Question
from core.models.llm_outputs import FSRSScore
from core.monitoring.logger import get_logger

logger = get_logger(__name__)


class FeedbackError(Exception):
    """Custom exception for errors during feedback generation."""

    pass


class FeedbackService:
    """
    This service is responsible for generating helpful feedback for the user based
    on their answer and score.
    """

    def __init__(self, llm_provider: str = "openai"):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_feedback(self, question: Question, answer: str, score: FSRSScore) -> str:
        """
        Generates a conversational feedback message using an LLM.

        Args:
            question: The Question object that was answered.
            answer: The user's answer string.
            score: The FSRSScore object for the answer.

        Returns:
            A string containing the generated feedback for the user.

        Raises:
            ValueError: If the LLM call fails or returns invalid data
        """
        logger.info(f"Generating feedback for score: {score.score}/5...")

        prompt = self._build_feedback_prompt(question, answer, score)

        try:
            response = await self._call_openai_for_feedback(prompt)
            feedback = self._parse_feedback_response(response)

            logger.info(f"Generated feedback: {feedback[:100]}...")
            return feedback

        except Exception as e:
            error_msg = (
                f"Failed to generate feedback: {str(e)}. Please try again or contact support if the issue persists."
            )
            logger.error(f"Error generating feedback: {str(e)}")
            raise ValueError(error_msg) from e

    def _build_feedback_prompt(self, question: Question, answer: str, score: FSRSScore) -> str:
        """Creates a prompt for generating contextual feedback."""

        feedback_strategy = self._get_feedback_strategy(score.score)

        return f"""You are Spaced, a friendly and encouraging AI tutor. Generate helpful feedback for a student's answer.

CONTEXT:
Question: {question.text}
Topic: {getattr(question, 'topic', 'General')}
Difficulty: {question.difficulty}/5

STUDENT'S ANSWER:
{answer}

EVALUATION:
Score: {score.score}/5
Reasoning: {score.reasoning}

FEEDBACK STRATEGY FOR SCORE {score.score}:
{feedback_strategy}

GUIDELINES:
- Be conversational and encouraging, never harsh or discouraging
- Use the student's name sparingly (prefer "you" over names)
- For good answers (4-5): Give brief positive reinforcement
- For poor answers (1-3): Provide helpful hints without giving away the complete answer
- Keep feedback concise but meaningful (2-4 sentences)
- End with a question or prompt that guides them forward when appropriate
- Match the educational level of the original question

Generate feedback that will help the student learn and stay motivated:"""

    def _get_feedback_strategy(self, score: int) -> str:
        """Returns the appropriate feedback strategy based on score."""
        strategies = {
            5: """EXCELLENT ANSWER - Give enthusiastic praise and perhaps mention what made their answer particularly strong. Keep it brief since they clearly understand the concept.""",
            4: """GOOD ANSWER - Give positive reinforcement and acknowledge their understanding. You might mention one small area for enhancement or ask a follow-up question to deepen their thinking.""",
            3: """ACCEPTABLE ANSWER - Give encouragement for what they got right, then provide a gentle hint about what they missed or could improve. Guide them toward a more complete understanding.""",
            2: """PARTIALLY CORRECT - Acknowledge any correct elements in their answer, then provide a helpful hint that guides them toward the key concept they missed. Encourage them to try again.""",
            1: """INCORRECT ANSWER - Be gentle and encouraging. Provide a helpful hint that points them toward the right direction without giving away the answer. Focus on one key concept they need to grasp.""",
        }
        return strategies.get(score, strategies[3])

    async def _call_openai_for_feedback(self, prompt: str) -> str:
        """Makes the OpenAI API call for feedback generation."""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using cheaper model for testing
                messages=[
                    {
                        "role": "system",
                        "content": "You are Spaced, a friendly AI tutor who provides encouraging and helpful feedback. Always respond with natural, conversational feedback.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=250,
                temperature=0.7,  # Higher temperature for more natural conversation
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty response")

            return content.strip()

        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise ValueError(f"Unable to generate feedback due to AI service error: {str(e)}") from e

    def _parse_feedback_response(self, response: str) -> str:
        """Parses and cleans the LLM response."""
        # Clean up the response
        feedback = response.strip()

        # Remove any JSON formatting if accidentally included
        if feedback.startswith("{") and feedback.endswith("}"):
            try:
                data = json.loads(feedback)
                feedback = data.get("feedback", feedback)
            except json.JSONDecodeError:
                pass  # Just use the original response

        # Ensure reasonable length
        if len(feedback) > 500:
            feedback = feedback[:500] + "..."

        # Validate that we got meaningful feedback
        if len(feedback.strip()) < 10:
            raise ValueError("AI generated feedback that is too short to be helpful")

        return feedback
