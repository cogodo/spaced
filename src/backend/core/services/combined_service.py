from typing import Any, Dict, Optional

from app.config import settings
from core.llm import get_llm_provider
from core.models import Question
from core.models.llm_outputs import CombinedTurnPayload, NextAction
from core.monitoring.logger import get_logger

logger = get_logger(__name__)


class CombinedServiceError(Exception):
    """Custom exception for combined tutor+scorer service."""

    pass


class CombinedService:
    """
    One-pass tutor + scorer. Returns a conversational reply and state update JSON.

    Expected JSON schema:
    {
      "user_facing_response": "string",
      "state_update": {
        "score": 1,
        "reasoning": "string",
        "hint_given": false,
        "misconception": "string|null",
        "next_action": "next_question|clarification|end_chat"
      }
    }
    """

    def __init__(self):
        self.llm_provider = get_llm_provider("default")

    async def evaluate_turn(
        self, question: Question, answer: str, after_hint: bool, initial_score: Optional[int] = None
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(question, answer, after_hint, initial_score)
        try:
            data = await self.llm_provider.complete_structured(
                prompt=prompt,
                response_model=CombinedTurnPayload,
                system_prompt="You are a helpful tutor and grader. Always return a valid JSON object per schema.",
                max_tokens=600,
                timeout=float(settings.anthropic_request_timeout_seconds),
            )
            payload = self._parse_response(data)
            return payload
        except Exception as e:
            logger.error(f"CombinedService evaluate_turn failed: {e}")
            raise CombinedServiceError(str(e)) from e

    def _build_prompt(self, question: Question, answer: str, after_hint: bool, initial_score: Optional[int]) -> str:
        return f"""
SYSTEM:
You are a tutoring assistant and grader for spaced repetition. Primary objective: assign the most accurate FSRS score (1-5) based on the conversation history and the rubric. Output JSON ONLY per the schema.

USER:
Role & capabilities:
- Be a friendly tutor. You can ask a guiding question or give a short hint.
- Do not reveal full solutions.
- Provide a concise reply (1-3 sentences) and an FSRS score with minimal reasoning.

Topic: {getattr(question, 'topic', 'General')}
Difficulty: {question.difficulty}/5
Question Type: {question.type}
Question: {question.text}

Question History:
{answer}

FSRS scoring quick guide (1-5):
1 = incorrect/no understanding
2 = mostly incorrect, major gaps
3 = partially correct or needed significant guidance
4 = correct with good understanding
5 = excellent clarity and depth

Rules:
- Prioritize scoring accuracy according to the rubric using the conversation history.
- user_facing_response: friendly, concise, and helpful.
- hint_given: true if you provided a hint or guiding question.
- next_action: "next_question" | "clarification" | "end_chat".
- reasoning: brief (<=200 chars). No chain-of-thought.

Return ONLY this JSON object:
{{
  "user_facing_response": "<string>",
  "state_update": {{
    "score": <integer 1-5>,
    "reasoning": "<string>",
    "hint_given": <true|false>,
    "misconception": "<string|null>",
    "next_action": "<next_question|clarification|end_chat>"
  }}
}}
"""

    def _parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Validate using Pydantic (data is already validated by complete_structured)
        try:
            payload = CombinedTurnPayload(**data)
        except Exception as e:
            raise ValueError(f"AI returned malformed response: {str(e)}")

        # Normalize enum to NextAction instance
        try:
            next_action = NextAction(payload.state_update.next_action)
        except Exception:
            raise ValueError("Invalid next_action value")

        return {
            "user_facing_response": payload.user_facing_response.strip(),
            "state_update": {
                "score": payload.state_update.score,
                "reasoning": payload.state_update.reasoning,
                "hint_given": payload.state_update.hint_given,
                "misconception": payload.state_update.misconception,
                "next_action": next_action,
            },
        }
