from core.models.llm_outputs import NextAction, RoutingDecision


class RoutingService:
    """
    This service is responsible for determining the user's intent to guide the
    conversation flow.
    """

    async def determine_next_action(self, user_response: str) -> RoutingDecision:
        """
        Determines the next action based on the user's response using an LLM.

        In this stubbed version, it uses simple keyword matching.

        Args:
            user_response: The user's latest message.

        Returns:
            A RoutingDecision object containing the classified next action.
        """
        # TODO: LLM call with structured output to be implemented in Phase 2.

        print(f"--- FAKE ROUTING: Determining next action for response: '{user_response[:50]}...'")

        response_lower = user_response.lower()
        next_action = NextAction.AWAIT_CLARIFICATION

        if "next" in response_lower or "move on" in response_lower:
            next_action = NextAction.MOVE_TO_NEXT_QUESTION
        elif "stop" in response_lower or "end" in response_lower:
            next_action = NextAction.END_CHAT

        mock_decision = RoutingDecision(next_action=next_action)

        print(f"--- FAKE ROUTING: Mocked decision is: {mock_decision.next_action.value}")
        return mock_decision
