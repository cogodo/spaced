import json
from typing import Tuple

from openai import AsyncOpenAI

from app.config import settings
from core.models import Question
from core.models.llm_outputs import ClarificationImpact
from core.monitoring.logger import get_logger

logger = get_logger(__name__)


class ClarificationService:
    """
    This service handles the flow where a user asks a clarifying question instead
    of answering the original question.
    """

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def handle_clarification(
        self, original_question: Question, user_clarification_request: str
    ) -> Tuple[str, ClarificationImpact]:
        """
        Generates an answer to the user's clarification question and assesses
        its impact on the original question's difficulty.

        Args:
            original_question: The question the user was supposed to answer.
            user_clarification_request: The user's actual question.

        Returns:
            A tuple containing:
            - The informative answer to the user's clarification question.
            - A ClarificationImpact object with the adjusted score.

        Raises:
            ValueError: If either LLM call fails or returns invalid data
        """
        logger.info(f"Handling clarification request: '{user_clarification_request[:50]}...'")

        try:
            # First LLM call: Generate the clarification answer
            clarification_answer = await self._generate_clarification_answer(
                original_question, user_clarification_request
            )

            # Second LLM call: Assess the impact
            impact = await self._assess_clarification_impact(
                original_question, user_clarification_request, clarification_answer
            )

            logger.info(f"Generated clarification answer: {clarification_answer[:100]}...")
            logger.info(f"Impact assessment: score {impact.adjusted_score}")

            return clarification_answer, impact

        except Exception as e:
            error_msg = f"Failed to handle clarification request: {str(e)}. Please try again or contact support if the issue persists."
            logger.error(f"Error handling clarification: {str(e)}")
            raise ValueError(error_msg) from e

    async def _generate_clarification_answer(self, original_question: Question, clarification_request: str) -> str:
        """Generates a helpful answer to the user's clarification question."""

        prompt = f"""You are Spaced, a helpful AI tutor. A student is working on a question but has asked for clarification instead of answering.

ORIGINAL QUESTION:
{original_question.text}

STUDENT'S CLARIFICATION REQUEST:
{clarification_request}

Your task is to provide a helpful, educational response to their clarification request.

GUIDELINES:
- Directly address the student's question or point of confusion.
- Be informative and helpful while maintaining educational value
- Don't give away the complete answer to the original question
- Provide enough context to help them understand the concept
- Use clear, accessible language appropriate for the learning level
- Keep the response concise but thorough (2-4 sentences)
- If they're asking about a term or concept, explain it clearly
- If they're asking for hints, provide gentle guidance without solving it for them

Provide a direct, helpful response to their clarification request:"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",  # Using cheaper model for testing
                messages=[
                    {
                        "role": "system",
                        "content": "You are Spaced, a helpful AI tutor. Provide clear, educational responses to student questions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty response for clarification")

            answer = content.strip()

            # Validate that we got meaningful clarification
            if len(answer) < 20:
                raise ValueError("AI generated clarification that is too short to be helpful")

            return answer

        except Exception as e:
            logger.error(f"Error generating clarification answer: {str(e)}")
            raise ValueError(f"Unable to generate clarification due to AI service error: {str(e)}") from e

    async def _assess_clarification_impact(
        self, original_question: Question, clarification_request: str, clarification_answer: str
    ) -> ClarificationImpact:
        """Assesses how much the clarification helps with the original question."""

        prompt = f"""You are an educational expert analyzing the impact of a clarification on a student's ability to answer the original question.

ORIGINAL QUESTION:
{original_question.text}

STUDENT'S CLARIFICATION REQUEST:
{clarification_request}

CLARIFICATION ANSWER PROVIDED:
{clarification_answer}

Assess how much this clarification helps the student answer the original question:

IMPACT LEVELS:
- Score 1: The clarification essentially gives away the answer or makes it trivially easy
- Score 3: The clarification provides helpful context but the student still needs to think and apply knowledge

ASSESSMENT CRITERIA:
- Does the clarification reveal key concepts needed for the answer?
- How much thinking/application is still required after this help?
- Would a student be able to answer correctly just from this clarification?

Provide your assessment as a JSON object:
{{
    "adjusted_score": <1 or 3>,
    "reasoning": "<brief explanation of why this score was assigned>"
}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",  # Using cheaper model for testing
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educational expert who assesses the impact of clarifications on learning. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty response for impact assessment")

            # Parse and validate the response
            data = json.loads(content)

            if "adjusted_score" not in data or "reasoning" not in data:
                raise ValueError("AI response missing required fields (adjusted_score and reasoning)")

            score = int(data["adjusted_score"])
            if score not in [1, 3]:
                raise ValueError(f"AI returned invalid adjusted_score {score}, must be 1 or 3")

            return ClarificationImpact(adjusted_score=score, reasoning=str(data["reasoning"]))

        except Exception as e:
            logger.error(f"Error assessing clarification impact: {str(e)}")
            raise ValueError(f"Unable to assess clarification impact due to AI service error: {str(e)}") from e
