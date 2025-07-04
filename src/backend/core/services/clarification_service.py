from typing import Tuple

from core.models import Question
from core.models.llm_outputs import ClarificationImpact


class ClarificationService:
    """
    This service handles the flow where a user asks a clarifying question instead
    of answering the original question.
    """

    async def handle_clarification(
        self, original_question: Question, user_clarification_request: str
    ) -> Tuple[str, ClarificationImpact]:
        """
        Generates an answer to the user's clarification question and assesses
        its impact on the original question's difficulty.

        In this stubbed version, it returns a hardcoded response and impact assessment.

        Args:
            original_question: The question the user was supposed to answer.
            user_clarification_request: The user's actual question.

        Returns:
            A tuple containing:
            - The informative answer to the user's clarification question.
            - A ClarificationImpact object with the adjusted score.
        """
        # TODO: Two LLM calls to be implemented in Phase 2.
        # 1. Generate the answer to the user_clarification_request.
        # 2. Assess the impact of that answer on the original_question.

        print(f"--- FAKE CLARIFICATION: Handling clarification request: '{user_clarification_request[:50]}...'")

        mock_answer = (
            "This is a mocked answer to your clarification question. It provides some helpful, adjacent information."
        )
        mock_impact = ClarificationImpact(
            adjusted_score=3,
            reasoning="The mocked clarification provides a hint but does not fully answer the original question.",
        )

        print(f"--- FAKE CLARIFICATION: Mocked answer: '{mock_answer}'")
        print(f"--- FAKE CLARIFICATION: Mocked impact score is {mock_impact.adjusted_score}")

        return mock_answer, mock_impact
