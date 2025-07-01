from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from app.config import settings
from core.models.conversation import (
    ConversationState,
    LLMResponse,
    LLMStateUpdate,
    Turn,
)
from core.repositories.question_repository import QuestionRepository
from core.repositories.topic_repository import TopicRepository
from core.services.question_service import QuestionService
from infrastructure.redis.session_manager import RedisSessionManager

# --- LLM Interaction Models ---


class ConversationService:
    """
    Manages the one-question-per-call conversation flow.
    """

    def __init__(self):
        self.redis_manager = RedisSessionManager()
        self.question_service = QuestionService()
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.topic_repo = TopicRepository()
        self.question_repo = QuestionRepository()

    async def process_turn(
        self, user_id: str, session_id: str, user_input: str
    ) -> Turn:
        try:
            state = await self.get_or_create_state(user_id, session_id)
            prompt = self._build_prompt(state, user_input)
            llm_response_str = await self._call_llm(prompt)
            llm_response = LLMResponse.model_validate_json(llm_response_str)
            response_text = llm_response.user_facing_response

            # The LLM decides if we should move to the next question by including a
            # token.
            if "[NEXT_QUESTION]" in response_text:
                state = self._update_state(
                    state=state,
                    llm_response=llm_response,
                    user_input=user_input,
                    is_sufficient=True,
                )

                # Check for topic completion before getting the next question
                if state.question_index >= len(state.question_ids):
                    response_text = response_text.replace(
                        "[NEXT_QUESTION]",
                        (
                            "\\n\\nCongratulations, you've completed all questions for "
                            "this topic!"
                        ),
                    )
                else:
                    next_question = await self.question_repo.get_by_id(
                        user_id=user_id,
                        topic_id=state.topic_id,
                        question_id=state.question_ids[state.question_index],
                    )
                    response_text = response_text.replace(
                        "[NEXT_QUESTION]",
                        f"\\n\\n**Next Question:** {next_question.text}",
                    )
            else:
                state = self._update_state(
                    state=state,
                    llm_response=llm_response,
                    user_input=user_input,
                    is_sufficient=False,
                )

            await self._save_state(user_id, session_id, state)
            return Turn(bot_response=response_text, state=state)

        except ValueError as e:
            # Catches errors like topic not found in _get_or_create_state,
            # or other value errors like no questions found.
            print(f"Error processing turn: {e}")
            return Turn(
                bot_response=(
                    "I'm having a bit of trouble with this topic. It seems there are "
                    "no questions available. Please try another topic."
                ),
                state=None,
            )
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return Turn(
                bot_response=(
                    "I'm sorry, an unexpected error occurred. Please try again later."
                ),
                state=None,
            )

    async def end_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Ends the session, calculates analytics, and cleans up the state from Redis.
        """
        state = await self.redis_manager.get_conversation_state(user_id, session_id)

        if not state:
            # If state doesn't exist, it might have expired or was never created.
            # Return a default/empty analytics object.
            return {
                "final_score": 0.0,
                "questions_answered": 0,
                "total_questions": 0,
                "percentage_score": 0,
            }

        questions_answered = len(state.answered_question_ids)
        total_questions = len(state.question_ids)

        if not state.score_history:
            final_score = 0.0
        else:
            final_score = sum(state.score_history) / len(state.score_history)

        percentage_score = int((final_score / 5) * 100) if final_score > 0 else 0

        # Clean up the session state from Redis
        await self.redis_manager.delete_conversation_state(user_id, session_id)

        return {
            "final_score": round(final_score, 2),
            "questions_answered": questions_answered,
            "total_questions": total_questions,
            "percentage_score": percentage_score,
        }

    async def get_or_create_state(
        self, user_id: str, session_id: str, topic_id: Optional[str] = None
    ) -> ConversationState:
        """Creates a new conversation state for the user's session."""
        if topic_id is None:
            topic_id = await self.topic_repo.get_default_topic_id()
        questions = await self.question_service.get_topic_questions(topic_id, user_id)
        if not questions:
            raise ValueError(
                f"No questions found for topic ID '{topic_id}'. Cannot start "
                "conversation."
            )
        question_ids = [q.id for q in questions]
        return ConversationState(
            user_id=user_id,
            topic_id=topic_id,
            question_ids=question_ids,
        )

    def _update_state(
        self, state: ConversationState, update: LLMStateUpdate, question_id: str
    ) -> ConversationState:
        """Updates the conversation state based on the LLM response."""
        state.score_history.append(update.score)
        if update.hint_given:
            state.hints_given += 1
        if update.misconception:
            state.misconceptions.append(update.misconception)

        state.answered_question_ids.append(question_id)
        state.turn_count += 1
        return state

    def _build_prompt(
        self, state: ConversationState, user_input: str, is_json_mode: bool = True
    ) -> str:
        """Constructs the full prompt for the LLM."""
        context = self._get_context(state)
        history = self._format_history(state)
        prompt = f"""
{context}

{history}

Here are the rules you MUST follow:
1. Evaluate the student's answer for the CURRENT QUESTION.
2. Provide a conversational response that integrates praise or correction.
3. If the student's answer is sufficient, end your response with the exact token:
   [NEXT_QUESTION]
4. If the student's answer is insufficient, ask a clarifying question or provide a
   hint about the CURRENT QUESTION. Do NOT include the token.

Return your entire response as a single JSON object with two keys:
- "user_facing_response": A string containing your conversational reply to the
  student. This is where you will include the [NEXT_QUESTION] token if
  appropriate.
- "state_update": A JSON object with the following keys:
    - "score": An integer score from 0-5 for the student's answer.
    - "hint_given": A boolean, true if you provided a hint.
    - "misconception": A brief string summarizing any misconception you identified,
      or null if none.
"""
        return prompt

    def _get_context(self, state: ConversationState) -> str:
        """Returns the contextual part of the prompt."""
        question_text = state.questions[state.question_index].text
        return f"CURRENT QUESTION: {question_text}"

    def _format_history(self, state: ConversationState) -> str:
        """Formats the conversation history for the prompt."""
        history = ""
        for turn in state.history:
            history += f"Human: {turn.user_input}\\nAI: {turn.bot_response}\\n"
        return history

    def _get_summary(self, state: ConversationState) -> str:
        """Generates a summary of the user's performance so far."""
        total_questions = len(state.score_history)
        if total_questions == 0:
            return "This is the first question of the session."

        correct_answers = sum(1 for score in state.score_history if score >= 3)

        summary = (
            f"You're tutoring a student who's answered {total_questions} "
            f"questions ({correct_answers} correct)."
        )

        if state.hints_given > 0:
            summary += (
                f" You've provided hints on {state.hints_given} of those questions."
            )

        if any(state.misconceptions):
            summary += " Be mindful of the student's previous misconceptions."

        return summary

    async def _call_llm(self, prompt: str) -> str:
        """Calls the OpenAI API and returns the response content."""
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Using a more advanced model
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Spaced, a friendly conversational tutor who always "
                        "responds in the specified JSON format."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    async def _save_state(
        self, user_id: str, session_id: str, state: ConversationState
    ):
        await self.redis_manager.store_conversation_state(user_id, session_id, state)
