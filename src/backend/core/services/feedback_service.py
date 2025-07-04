from core.models import Question
from core.models.llm_outputs import FSRSScore


class FeedbackService:
    """
    This service is responsible for generating helpful feedback for the user based
    on their answer and score.
    """

    async def generate_feedback(self, question: Question, answer: str, score: FSRSScore) -> str:
        """
        Generates a conversational feedback message using an LLM.

        In this stubbed version, it returns a hardcoded message based on the score.

        Args:
            question: The Question object that was answered.
            answer: The user's answer string.
            score: The FSRSScore object for the answer.

        Returns:
            A string containing the generated feedback for the user.
        """
        # TODO: LLM call to be implemented in Phase 2.
        # The prompt will include the question, answer, score, and reasoning
        # to generate a helpful, conversational hint or acknowledgment.

        print(f"--- FAKE FEEDBACK: Generating feedback for score: {score.score}...")

        if score.score >= 4:
            mock_feedback = "That's a great answer! Nicely done."
        else:
            mock_feedback = "That's a good start, but let's think about it a bit more. What about the other aspects of the topic? (This is a mocked hint.)"

        print(f"--- FAKE FEEDBACK: Mocked feedback is: '{mock_feedback}'")
        return mock_feedback
