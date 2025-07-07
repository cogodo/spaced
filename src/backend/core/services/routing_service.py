import json

from openai import AsyncOpenAI

from app.config import settings
from core.models.llm_outputs import NextAction, RoutingDecision
from core.monitoring.logger import get_logger

logger = get_logger(__name__)


class RoutingService:
    """
    This service is responsible for determining the user's intent to guide the
    conversation flow.
    """

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def determine_next_action(self, user_response: str) -> RoutingDecision:
        """
        Determines the next action based on the user's response using an LLM.

        Args:
            user_response: The user's latest message.

        Returns:
            A RoutingDecision object containing the classified next action.

        Raises:
            ValueError: If the LLM call fails or returns invalid data
        """
        logger.info(f"Determining next action for response: '{user_response[:50]}...'")

        prompt = self._build_routing_prompt(user_response)

        try:
            response = await self._call_openai_for_routing(prompt)
            decision_data = self._parse_routing_response(response)

            # Create and validate RoutingDecision object
            decision = RoutingDecision(**decision_data)

            logger.info(f"Determined next action: {decision.next_action.value}")
            return decision

        except Exception as e:
            error_msg = (
                f"Failed to determine next action: {str(e)}. Please try again or contact support if the issue persists."
            )
            logger.error(f"Error determining next action: {str(e)}")
            raise ValueError(error_msg) from e

    def _build_routing_prompt(self, user_response: str) -> str:
        """Creates a prompt for intent classification."""

        return f"""You are an AI assistant that classifies user responses in an educational chat session.

The user has just received feedback on their answer to a question and is now responding. You need to determine their intent from their response.

USER'S RESPONSE:
"{user_response}"

CLASSIFICATION OPTIONS:
1. "next_question" - User wants to move on to the next question
   Examples: "next", "let's move on", "I'm ready for the next one", "got it, what's next?", "continue"

2. "end_chat" - User wants to end the session
   Examples: "stop", "I'm done", "end session", "quit", "that's enough for now", "goodbye"

3. "clarification" - User is asking for clarification, help, or has a question
   Examples: "I don't understand", "can you explain?", "what does X mean?", "how do you...?", "why is...?"

CLASSIFICATION RULES:
- If the response contains clear indicators of wanting to proceed (next, continue, ready), choose "next_question"
- If the response contains clear indicators of wanting to stop (stop, end, done, quit), choose "end_chat"
- If the response is a question, asks for help, or expresses confusion, choose "clarification"
- For ambiguous responses, default to "clarification" to be helpful
- If the response appears to be a direct answer to the question, choose "answer_question"

Respond with a JSON object containing exactly this field:
{{
    "next_action": "<next_question|end_chat|clarification>"
}}"""

    async def _call_openai_for_routing(self, prompt: str) -> str:
        """Makes the OpenAI API call for intent classification."""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using cheaper model for testing
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at classifying user intent in educational conversations. Always respond with valid JSON containing a 'next_action' field.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.1,  # Very low temperature for consistent classification
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty response")

            return content

        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise ValueError(f"Unable to classify user intent due to AI service error: {str(e)}") from e

    def _parse_routing_response(self, response: str) -> dict:
        """Parses the LLM response into a structured format."""
        try:
            data = json.loads(response)

            if "next_action" not in data:
                raise ValueError("AI response missing required 'next_action' field")

            action_value = data["next_action"]

            # Validate action is one of the allowed values
            valid_actions = [action.value for action in NextAction]
            if action_value not in valid_actions:
                raise ValueError(f"AI returned invalid action '{action_value}', must be one of {valid_actions}")

            return {"next_action": NextAction(action_value)}

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse routing response: {str(e)}")
            logger.error(f"Response was: {response}")
            raise ValueError(f"AI returned malformed response: {str(e)}") from e
