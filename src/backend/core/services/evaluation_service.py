from core.models import Question
from core.models.llm_outputs import FSRSScore


class EvaluationService:
    """
    This service is responsible for evaluating a user's answer against a question.
    """

    async def score_answer(self, question: Question, answer: str, after_hint: bool) -> FSRSScore:
        """
        Scores a user's answer using an LLM.

        In this stubbed version, it returns a hardcoded score.

        Args:
            question: The Question object being answered.
            answer: The user's answer string.
            after_hint: Boolean indicating if the user received a hint.

        Returns:
            An FSRSScore object containing the score and reasoning.
        """
        # TODO: LLM call to be implemented in Phase 2.
        # The prompt will include the question, the user's answer,
        # the FSRS scoring guide, and whether a hint was provided.

        print(f"--- FAKE SCORING: Scoring answer for question: {question.text[:50]}...")
        print(f"--- FAKE SCORING: User answer: {answer[:50]}...")

        # Mocked response: Return a "good" score.
        mock_score = FSRSScore(
            score=4, reasoning="This is a mocked response. The answer appears to be correct and well-explained."
        )

        print(f"--- FAKE SCORING: Mocked score is {mock_score.score} with reasoning: '{mock_score.reasoning}'")
        return mock_score
