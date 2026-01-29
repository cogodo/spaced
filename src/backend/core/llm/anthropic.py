"""Anthropic Claude LLM provider implementation."""

import asyncio
import json
import re
from typing import Any, AsyncGenerator, Dict, Optional, Type

from pydantic import BaseModel, ValidationError

from app.config import settings
from core.llm.base import LLMProvider
from core.monitoring.logger import get_logger

logger = get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider.

    Handles text completion and structured JSON output with retry logic
    and JSON extraction fallbacks.
    """

    def __init__(self, model: str):
        """Initialize the Anthropic provider.

        Args:
            model: The Anthropic model identifier (e.g., 'claude-sonnet-4-20250514').
        """
        from anthropic import AsyncAnthropic

        self.model = model
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.max_retries = settings.anthropic_max_retries

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> str:
        """Generate a text completion using Claude.

        Args:
            prompt: The user prompt/input.
            system_prompt: Optional system instructions.
            max_tokens: Maximum tokens in the response.
            timeout: Request timeout in seconds.

        Returns:
            The generated text response.

        Raises:
            Exception: If the API call fails after retries.
        """
        timeout = timeout or float(settings.anthropic_request_timeout_seconds)
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if system_prompt:
                    kwargs["system"] = system_prompt

                response = await asyncio.wait_for(
                    self.client.messages.create(**kwargs),
                    timeout=timeout,
                )

                # Extract text from response
                content = response.content
                if content and len(content) > 0:
                    text_block = content[0]
                    if hasattr(text_block, "text"):
                        return text_block.text

                raise ValueError("Anthropic returned empty response")

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(f"Anthropic request timed out (attempt {attempt + 1})")
            except Exception as e:
                last_error = e
                logger.warning(f"Anthropic request failed (attempt {attempt + 1}): {e}")

            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))

        raise Exception(f"Anthropic request failed after {self.max_retries + 1} attempts: {last_error}")

    async def complete_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """Generate a structured JSON completion using Claude.

        Since Anthropic lacks native JSON mode, this method:
        1. Appends JSON instructions to the prompt
        2. Parses the response with json.loads()
        3. Falls back to regex extraction if direct parse fails
        4. Validates with the provided Pydantic model
        5. Retries on parse failure

        Args:
            prompt: The user prompt/input with JSON schema instructions.
            response_model: Pydantic model for validating the response.
            system_prompt: Optional system instructions.
            max_tokens: Maximum tokens in the response.
            timeout: Request timeout in seconds.

        Returns:
            Parsed and validated dictionary matching the response model.

        Raises:
            ValueError: If JSON parsing or validation fails after retries.
        """
        # Enhance system prompt with JSON instructions
        json_system = (system_prompt or "") + (
            "\n\nIMPORTANT: You must respond with ONLY a valid JSON object. "
            "No markdown code fences, no explanatory text before or after. "
            "Just the raw JSON object starting with { and ending with }."
        )

        timeout = timeout or float(settings.anthropic_request_timeout_seconds)
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                # Get raw response
                raw_response = await self.complete(
                    prompt=prompt,
                    system_prompt=json_system,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )

                # Try to parse JSON
                data = self._extract_json(raw_response)

                # Validate with Pydantic model
                validated = response_model(**data)
                return validated.model_dump()

            except json.JSONDecodeError as e:
                last_error = ValueError(f"Failed to parse JSON: {e}")
                logger.warning(f"JSON parse failed (attempt {attempt + 1}): {e}")
            except ValidationError as e:
                last_error = ValueError(f"Response validation failed: {e}")
                logger.warning(f"Pydantic validation failed (attempt {attempt + 1}): {e}")
            except Exception as e:
                last_error = e
                logger.warning(f"Structured completion failed (attempt {attempt + 1}): {e}")

            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))

        raise ValueError(f"Failed to get valid structured response after {self.max_retries + 1} attempts: {last_error}")

    async def complete_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """Stream text tokens as they're generated.

        Uses Anthropic's streaming API to yield text chunks in real-time.

        Args:
            prompt: The user prompt/input.
            system_prompt: Optional system instructions.
            max_tokens: Maximum tokens in the response.

        Yields:
            Text chunks as they're generated by the model.

        Raises:
            Exception: If the API call fails.
        """
        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic streaming request failed: {e}")
            raise

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text, handling various formats.

        Args:
            text: Raw text that may contain JSON.

        Returns:
            Parsed JSON dictionary.

        Raises:
            json.JSONDecodeError: If no valid JSON can be extracted.
        """
        text = text.strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Remove markdown code fences if present
        if text.startswith("```"):
            # Remove opening fence (with optional language specifier)
            text = re.sub(r"^```(?:json)?\s*\n?", "", text)
            # Remove closing fence
            text = re.sub(r"\n?```\s*$", "", text)
            try:
                return json.loads(text.strip())
            except json.JSONDecodeError:
                pass

        # Try to find JSON object with regex
        # Match outermost braces, handling nested structures
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # Last resort: find the last complete JSON object
        # This handles cases where there's text after the JSON
        last_brace = text.rfind("}")
        if last_brace != -1:
            first_brace = text.find("{")
            if first_brace != -1 and first_brace < last_brace:
                potential_json = text[first_brace : last_brace + 1]
                try:
                    return json.loads(potential_json)
                except json.JSONDecodeError:
                    pass

        raise json.JSONDecodeError("No valid JSON object found in response", text, 0)
