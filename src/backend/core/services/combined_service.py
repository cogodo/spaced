import json
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

from app.config import settings
from core.llm import get_llm_provider
from core.models import Question
from core.models.llm_outputs import CombinedTurnPayload, NextAction
from core.monitoring.logger import get_logger

logger = get_logger(__name__)

# Delimiter separating conversational response from state JSON in streaming mode
STATE_DELIMITER = "\n\n---STATE---\n"

# Characters that end a sentence for buffering purposes
SENTENCE_ENDINGS = {".", "!", "?"}

# Word-based chunking settings for smooth streaming UX
# Research shows 4-5 words at a time feels natural and responsive
WORDS_PER_CHUNK = 4


@dataclass
class StreamingResult:
    """Result from streaming evaluation containing text and state."""

    user_facing_response: str
    state_update: Dict[str, Any]


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

    async def evaluate_turn_streaming(
        self, question: Question, answer: str, after_hint: bool, initial_score: Optional[int] = None
    ) -> AsyncGenerator[Tuple[str, Optional[Dict[str, Any]]], None]:
        """
        Stream the turn evaluation, yielding sentences for TTS and returning state at the end.

        This method streams the conversational response sentence-by-sentence for low-latency TTS,
        then parses the state JSON after the delimiter.

        Yields:
            Tuple of (text_chunk, state_dict). text_chunk is a sentence for TTS.
            The final yield has state_dict populated with the parsed state.
            All intermediate yields have state_dict as None.

        Raises:
            CombinedServiceError: If streaming or parsing fails.
        """
        prompt = self._build_streaming_prompt(question, answer, after_hint, initial_score)
        system_prompt = (
            "You are a helpful tutor and grader. Follow the output format exactly: "
            "conversational response first, then the delimiter, then JSON state."
        )

        try:
            text_buffer = ""  # Buffer for accumulating words
            delimiter_found = False
            state_json = ""
            full_text = ""  # Track all text we've yielded

            async for token in self.llm_provider.complete_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=800,
            ):
                if not delimiter_found:
                    # Add token to buffer
                    text_buffer += token

                    # Check if delimiter has appeared in buffer
                    if STATE_DELIMITER in text_buffer:
                        delimiter_found = True
                        # Split at delimiter
                        text_part, json_part = text_buffer.split(STATE_DELIMITER, 1)
                        # Yield any remaining text before delimiter (preserve trailing space)
                        if text_part:
                            yield (text_part, None)
                            full_text += text_part
                        text_buffer = ""
                        state_json = json_part
                    else:
                        # Word-based chunking for smoother streaming UX
                        # Yield chunks of ~4 words at a time
                        chunks, text_buffer = self._extract_word_chunks(text_buffer)
                        for chunk in chunks:
                            yield (chunk, None)
                            full_text += chunk
                else:
                    # After delimiter, accumulate JSON
                    state_json += token

            # Yield any remaining text that wasn't chunked
            if not delimiter_found:
                # Delimiter never found - treat entire response as text, use defaults for state
                logger.warning("State delimiter not found in streaming response, using defaults")
                if text_buffer:
                    yield (text_buffer, None)
                # Return default state
                default_state = {
                    "score": 3,
                    "reasoning": "Unable to parse state from response",
                    "hint_given": False,
                    "misconception": None,
                    "next_action": NextAction.CLARIFICATION,
                }
                yield ("", default_state)
                return

            # Yield any remaining buffered text (preserving whitespace)
            if text_buffer:
                yield (text_buffer, None)

            # Parse the state JSON
            try:
                state_data = self._extract_json_from_text(state_json)
                parsed_state = self._parse_streaming_state(state_data)
                yield ("", parsed_state)
            except Exception as e:
                logger.error(f"Failed to parse state JSON: {e}, raw: {state_json[:200]}")
                # Return default state on parse failure
                default_state = {
                    "score": 3,
                    "reasoning": f"JSON parse error: {str(e)[:50]}",
                    "hint_given": False,
                    "misconception": None,
                    "next_action": NextAction.CLARIFICATION,
                }
                yield ("", default_state)

        except Exception as e:
            logger.error(f"CombinedService evaluate_turn_streaming failed: {e}")
            raise CombinedServiceError(str(e)) from e

    def _build_streaming_prompt(
        self, question: Question, answer: str, after_hint: bool, initial_score: Optional[int]
    ) -> str:
        """Build prompt for streaming mode with text-first output format."""
        return f"""You are a tutoring assistant for spaced repetition learning.

CONTEXT:
Topic: {getattr(question, 'topic', 'General')}
Difficulty: {question.difficulty}/5
Question Type: {question.type}
Question: {question.text}

Conversation History:
{answer}

YOUR TASK:
1. First, write your conversational response to the student (1-3 sentences). Be friendly and helpful.
   - If they answered correctly, praise them and confirm the key concept.
   - If they need help, provide a hint or ask a guiding question (don't reveal the full answer).

2. After your response, output EXACTLY this delimiter on its own line:

---STATE---

3. Then output the state JSON (no markdown code fences):
{{
  "score": <integer 1-5>,
  "reasoning": "<brief explanation, max 200 chars>",
  "hint_given": <true if you gave a hint, false otherwise>,
  "misconception": "<string describing any misconception, or null>",
  "next_action": "<one of: next_question, clarification, end_chat>"
}}

FSRS Scoring Guide:
1 = incorrect/no understanding
2 = mostly incorrect, major gaps
3 = partially correct or needed guidance
4 = correct with good understanding
5 = excellent clarity and depth

IMPORTANT:
- Write the conversational response FIRST, naturally, as you would speak to a student.
- Then the delimiter ---STATE--- on its own line.
- Then the JSON state object.
- Do NOT use markdown code fences around the JSON."""

    def _extract_word_chunks(self, text: str) -> Tuple[list, str]:
        """
        Extract chunks of words from text buffer for smooth streaming.

        Uses word-based chunking (~4 words at a time) which research shows
        provides the best UX for streaming text - more responsive than
        sentence-based but not as choppy as character-by-character.

        Returns:
            Tuple of (list of word chunks with preserved spacing, remaining buffer text)
        """
        chunks = []

        # Split into words while preserving spacing information
        # We want to keep the exact spacing to avoid "space being cut off" issues
        words_with_spaces = []
        current_word = ""
        for char in text:
            if char in " \t\n":
                if current_word:
                    words_with_spaces.append(current_word)
                    current_word = ""
                words_with_spaces.append(char)  # Keep the space as its own "word"
            else:
                current_word += char

        # Don't include the last incomplete word in chunks - keep it in buffer
        # Count actual words (not spaces)
        actual_words = [w for w in words_with_spaces if w.strip()]
        num_complete_words = len(actual_words)

        # We need at least WORDS_PER_CHUNK words to emit a chunk
        # Keep the last partial word in buffer
        if current_word:
            # There's an incomplete word at the end
            num_complete_words = len(actual_words)
        else:
            num_complete_words = len(actual_words)

        # Calculate how many complete chunks we can emit
        words_to_emit = (num_complete_words // WORDS_PER_CHUNK) * WORDS_PER_CHUNK

        if words_to_emit > 0:
            # Rebuild the text up to words_to_emit actual words
            emitted_word_count = 0
            emit_end_idx = 0

            for i, item in enumerate(words_with_spaces):
                if item.strip():  # It's a word, not whitespace
                    emitted_word_count += 1
                    if emitted_word_count >= words_to_emit:
                        emit_end_idx = i + 1
                        break
                emit_end_idx = i + 1

            # Build the chunk string
            chunk = "".join(words_with_spaces[:emit_end_idx])
            if chunk:
                chunks.append(chunk)

            # Remaining is everything after, plus any incomplete word
            remaining_parts = words_with_spaces[emit_end_idx:]
            remaining = "".join(remaining_parts) + current_word
        else:
            # Not enough words yet, keep everything in buffer
            remaining = text

        return chunks, remaining

    def _extract_sentences(self, text: str) -> Tuple[list, str]:
        """
        Extract complete sentences from text buffer.
        (Kept for potential future use, but word chunking is preferred for streaming)

        Returns:
            Tuple of (list of complete sentences, remaining buffer text)
        """
        sentences = []
        remaining = text

        while True:
            # Find the earliest sentence ending
            earliest_idx = -1
            for ending in SENTENCE_ENDINGS:
                idx = remaining.find(ending)
                if idx != -1:
                    # Check if followed by space or newline (to avoid abbreviations like "Dr.")
                    if idx + 1 < len(remaining) and remaining[idx + 1] in " \n\t":
                        if earliest_idx == -1 or idx < earliest_idx:
                            earliest_idx = idx

            if earliest_idx == -1:
                # No complete sentence found
                break

            # Extract the sentence (including the ending punctuation and trailing space)
            sentence = remaining[: earliest_idx + 2]  # Include the space after punctuation
            if sentence.strip():
                sentences.append(sentence)
            remaining = remaining[earliest_idx + 2 :]

        return sentences, remaining

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON object from text, handling various formats."""
        text = text.strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Remove markdown code fences if present
        if text.startswith("```"):
            import re

            text = re.sub(r"^```(?:json)?\s*\n?", "", text)
            text = re.sub(r"\n?```\s*$", "", text)
            try:
                return json.loads(text.strip())
            except json.JSONDecodeError:
                pass

        # Try to find JSON object with braces
        import re

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise json.JSONDecodeError("No valid JSON object found", text, 0)

    def _parse_streaming_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate state data from streaming response."""
        # Extract and validate fields with defaults
        score = data.get("score", 3)
        if not isinstance(score, int) or score < 1 or score > 5:
            score = 3

        reasoning = data.get("reasoning", "")
        hint_given = bool(data.get("hint_given", False))
        misconception = data.get("misconception")

        # Parse next_action
        next_action_str = data.get("next_action", "clarification")
        try:
            next_action = NextAction(next_action_str)
        except ValueError:
            next_action = NextAction.CLARIFICATION

        return {
            "score": score,
            "reasoning": str(reasoning)[:200],
            "hint_given": hint_given,
            "misconception": misconception,
            "next_action": next_action,
        }
