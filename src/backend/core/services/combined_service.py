import json
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from app.config import settings
from core.models import Question
from core.models.llm_outputs import CombinedTurnPayload, NextAction
from core.models.profiles import CONVERSATION_STEP
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
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def evaluate_turn(
        self, question: Question, answer: str, after_hint: bool, initial_score: Optional[int] = None
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(question, answer, after_hint, initial_score)
        try:
            content = await self._call_openai(prompt)
            payload = self._parse_response(content)
            return payload
        except Exception as e:
            logger.error(f"CombinedService evaluate_turn failed: {e}")
            raise CombinedServiceError(str(e)) from e

    def _build_prompt(self, question: Question, answer: str, after_hint: bool, initial_score: Optional[int]) -> str:
        hint_context = "true" if after_hint else "false"
        previous_attempt = (
            f"Previous attempt score (first try): {initial_score}/5\n"
            if after_hint and initial_score is not None
            else ""
        )
        return f"""
SYSTEM:
You are a helpful tutor and grader using FSRS (1–5). Respond as JSON ONLY per the schema below; no extra text.

USER:
Topic: {getattr(question, 'topic', 'General')}
Difficulty: {question.difficulty}/5
Question Type: {question.type}
Question: {question.text}

Student Answer: {answer}
After Hint? {hint_context}
{previous_attempt}

FSRS rubric (1-5): 1=incorrect; 2=mostly incorrect; 3=mostly correct or correct after significant hint; 4=correct with good understanding; 5=excellent clarity and depth.

Rules:
- If After Hint? is true, maximum score is 4.
- Do not reveal the full answer. Offer one hint or guiding question if needed.
- user_facing_response: 1–3 sentences, friendly and concise.
- hint_given: true if you provided a hint or guiding question.
- next_action: "next_question" (if ready to move on), "clarification" (needs guidance), or "end_chat" (user wants to stop).
- reasoning: brief justification (<=200 chars). No chain-of-thought.

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

    async def _call_openai(self, prompt: str) -> str:
        used_model = settings.openai_model or "gpt-4o"
        is_gpt5 = "gpt-5" in (used_model or "").lower()
        max_val = min(CONVERSATION_STEP.max_completion_tokens, 600)

        # Simple retries with backoff
        attempts = 0
        last_error = None
        import asyncio

        while attempts <= settings.openai_max_retries:
            try:
                # Prefer Responses API for all models first
                try:
                    resp = await asyncio.wait_for(
                        self.openai_client.responses.create(
                            model=used_model,
                            instructions=(
                                "You are a helpful tutor and grader. Always return a valid JSON object per schema."
                            ),
                            input=prompt,
                            response_format={"type": "json_object"},
                            max_output_tokens=max_val,
                        ),
                        timeout=float(settings.openai_request_timeout_seconds),
                    )
                    content = getattr(resp, "output_text", None)
                    if not content:
                        # Conservative fallback extraction
                        content = None
                        outputs = getattr(resp, "output", None) or getattr(resp, "outputs", None)
                        if outputs and isinstance(outputs, list):
                            for out in outputs:
                                parts = getattr(out, "content", None)
                                if parts and isinstance(parts, list):
                                    for p in parts:
                                        t = getattr(p, "text", None)
                                        if isinstance(t, str) and t.strip():
                                            content = t
                                            break
                                    if content:
                                        break
                    # If Responses returned but content is still empty, try Chat fallback in the same attempt
                    if not content:
                        chat_kwargs = {
                            "model": used_model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are a helpful tutor and grader. Output valid JSON only.",
                                },
                                {"role": "user", "content": prompt},
                            ],
                            "response_format": {"type": "json_object"},
                        }
                        resp = await asyncio.wait_for(
                            self.openai_client.chat.completions.create(**chat_kwargs),
                            timeout=float(settings.openai_request_timeout_seconds),
                        )
                        if resp and getattr(resp, "choices", None):
                            msg = resp.choices[0].message
                            raw = getattr(msg, "content", None)
                            if isinstance(raw, str):
                                content = raw
                            elif isinstance(raw, list):
                                try:
                                    parts = []
                                    for part in raw:
                                        text_val = None
                                        if hasattr(part, "text"):
                                            text_val = getattr(part, "text", None)
                                        elif isinstance(part, dict):
                                            text_val = part.get("text")
                                        if isinstance(text_val, str) and text_val:
                                            parts.append(text_val)
                                    if parts:
                                        content = "".join(parts)
                                except Exception:
                                    content = None
                except Exception:
                    # Fallback to Chat Completions without explicit token caps
                    chat_kwargs = {
                        "model": used_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful tutor and grader. Output valid JSON only.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "response_format": {"type": "json_object"},
                    }
                    resp = await asyncio.wait_for(
                        self.openai_client.chat.completions.create(**chat_kwargs),
                        timeout=float(settings.openai_request_timeout_seconds),
                    )
                    # Extract content robustly: string or list-of-parts
                    content = None
                    if resp and getattr(resp, "choices", None):
                        msg = resp.choices[0].message
                        raw = getattr(msg, "content", None)
                        if isinstance(raw, str):
                            content = raw
                        elif isinstance(raw, list):
                            try:
                                parts = []
                                for part in raw:
                                    text_val = None
                                    if hasattr(part, "text"):
                                        text_val = getattr(part, "text", None)
                                    elif isinstance(part, dict):
                                        text_val = part.get("text")
                                    if isinstance(text_val, str) and text_val:
                                        parts.append(text_val)
                                if parts:
                                    content = "".join(parts)
                            except Exception:
                                content = None
                if not content or not isinstance(content, str) or not content.strip():
                    raise ValueError("OpenAI returned empty response")
                return content
            except Exception as e:
                last_error = e
                attempts += 1
                if attempts > settings.openai_max_retries:
                    break
                await asyncio.sleep(0.5 * attempts)
        raise ValueError(f"OpenAI request failed after retries: {str(last_error)}")

    def _parse_response(self, content: str) -> Dict[str, Any]:
        # Strict parse and validate using Pydantic
        try:
            data = json.loads(content)
        except Exception:
            # Conservative extraction attempt
            import re

            match = re.search(r"\{[\s\S]*\}\s*$", content)
            if not match:
                raise ValueError("Model did not return valid JSON object")
            data = json.loads(match.group(0))

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
