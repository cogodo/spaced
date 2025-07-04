from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from app.config import settings
from core.models.context import Context, TurnState
from core.models.conversation import (
    ConversationState,
    LLMResponse,
    Turn,
)
from core.models.llm_outputs import NextAction
from core.monitoring.logger import get_logger
from core.repositories.question_repository import QuestionRepository
from core.repositories.topic_repository import TopicRepository
from core.services.clarification_service import ClarificationService
from core.services.context_service import ContextService
from core.services.evaluation_service import EvaluationService
from core.services.feedback_service import FeedbackService
from core.services.question_service import QuestionService
from core.services.routing_service import RoutingService
from infrastructure.redis.session_manager import RedisSessionManager

logger = get_logger(__name__)

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
        self.context_service = ContextService()
        self.evaluation_service = EvaluationService()
        self.feedback_service = FeedbackService()
        self.routing_service = RoutingService()
        self.clarification_service = ClarificationService()

    async def process_turn(self, chat_id: str, user_uid: str, user_input: str) -> str:
        """
        Processes a single turn of the conversation, managing state and returning
        the next bot message.
        """
        logger.info(f"Processing turn for chat {chat_id}")
        context = await self.context_service.get_context(chat_id, user_uid)
        if not context:
            raise ValueError("Chat context not found.")

        # Main state machine logic
        if context.turnState == TurnState.AWAITING_INITIAL_ANSWER:
            return await self._handle_initial_answer(context, user_input)
        elif context.turnState == TurnState.AWAITING_FOLLOW_UP:
            return await self._handle_follow_up(context, user_input)
        elif context.turnState == TurnState.AWAITING_NEXT_ACTION:
            return await self._handle_next_action(context, user_input)
        else:
            raise ValueError(f"Invalid turn state: {context.turnState}")

    async def _handle_initial_answer(self, context: Context, user_input: str) -> str:
        """Handles the user's first answer to a question."""
        _, question = await self.context_service.get_current_question(context.chatId, context.userUid)
        if not question:
            return "It looks like we've run out of questions! Well done."

        score = await self.evaluation_service.score_answer(question, user_input, after_hint=False)
        feedback = await self.feedback_service.generate_feedback(question, user_input, score)

        if score.score >= 4:
            # Good answer, move to next question prompt
            context.scores[question.id] = score.score
            context.turnState = TurnState.AWAITING_NEXT_ACTION
            await self.context_service.repository.update(context.chatId, context.userUid, context.dict())
            return f"{feedback}\n\nReady for the next question, or do you have any questions about this one?"
        else:
            # Poor answer, await follow-up
            context.initialScore = score.score
            context.turnState = TurnState.AWAITING_FOLLOW_UP
            await self.context_service.repository.update(context.chatId, context.userUid, context.dict())
            return feedback

    async def _handle_follow_up(self, context: Context, user_input: str) -> str:
        """Handles the user's response after receiving a hint."""
        _, question = await self.context_service.get_current_question(context.chatId, context.userUid)
        if not question:
            return "Error: Could not find the current question."

        # Re-evaluate the answer, this time noting it's after a hint
        second_score = await self.evaluation_service.score_answer(question, user_input, after_hint=True)

        # Average the scores
        final_score = round((context.initialScore + second_score.score) / 2)
        context.scores[question.id] = final_score
        context.turnState = TurnState.AWAITING_NEXT_ACTION

        await self.context_service.repository.update(context.chatId, context.userUid, context.dict())

        return f"Thanks for the clarification! I've recorded a score of {final_score} for that question. Ready for the next one?"

    async def _handle_next_action(self, context: Context, user_input: str) -> str:
        """Handles the user's response when prompted for the next action."""
        decision = await self.routing_service.determine_next_action(user_input)

        if decision.next_action == NextAction.MOVE_TO_NEXT_QUESTION:
            context.questionIdx += 1
            context.initialScore = None
            context.turnState = TurnState.AWAITING_INITIAL_ANSWER
            await self.context_service.repository.update(context.chatId, context.userUid, context.dict())

            _, next_question = await self.context_service.get_current_question(context.chatId, context.userUid)
            if not next_question:
                return "You've completed all the questions! Great job."
            return f"Great, let's move on. Here is your next question:\n\n{next_question.text}"

        elif decision.next_action == NextAction.END_CHAT:
            context.end_session()
            await self.context_service.repository.update(context.chatId, context.userUid, context.dict())
            return "Got it. This chat session has now ended. Well done!"

        elif decision.next_action == NextAction.AWAIT_CLARIFICATION:
            _, question = await self.context_service.get_current_question(context.chatId, context.userUid)
            answer, impact = await self.clarification_service.handle_clarification(question, user_input)

            # If the clarification was very helpful, penalize score and move on
            if impact.adjusted_score == 1:
                context.scores[question.id] = 1
                context.turnState = TurnState.AWAITING_NEXT_ACTION
                await self.context_service.repository.update(context.chatId, context.userUid, context.dict())
                return f"{answer}\n\nSince that explanation was very direct, I've marked this question as needing more review later. Ready for the next question?"
            else:
                # Otherwise, just provide the info and wait for another attempt
                return f"{answer}\n\nDoes that help clarify things? Feel free to try answering the original question again."

    async def skip_question(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Skips the current question, updates the state, and returns the next question.
        """
        state = await self.redis_manager.get_conversation_state(user_id, session_id)
        if not state:
            raise ValueError("Conversation state not found.")

        # Mark current question as answered (skipped)
        state.answered_question_ids.append(state.question_ids[state.question_index])
        state.question_index += 1
        state.history.append(Turn(user_input="skip", bot_response="Question skipped."))

        # Save the updated state
        await self._save_state(user_id, session_id, state)

        # Check for completion
        if state.question_index >= len(state.question_ids):
            return {
                "is_done": True,
                "next_question": "Congratulations, you've completed all questions for this topic!",
            }

        # Get the next question
        next_question = await self.question_repo.get_by_id(
            user_id=user_id,
            topic_id=state.topic_id,
            question_id=state.question_ids[state.question_index],
        )

        return {"is_done": False, "next_question": next_question.text}

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
            raise ValueError(f"No questions found for topic ID '{topic_id}'. Cannot start conversation.")
        question_ids = [q.id for q in questions]
        return ConversationState(
            user_id=user_id,
            topic_id=topic_id,
            question_ids=question_ids,
            questions=questions,
        )

    def _update_state(
        self, state: ConversationState, llm_response: LLMResponse, user_input: str, is_sufficient: bool
    ) -> ConversationState:
        """Updates the conversation state based on the LLM response."""
        # Update history
        state.history.append(Turn(user_input=user_input, bot_response=llm_response.user_facing_response))
        state.turn_count += 1

        # Update scoring and metadata
        state.score_history.append(llm_response.state_update.score)
        if llm_response.state_update.hint_given:
            state.hints_given += 1
        if llm_response.state_update.misconception:
            state.misconceptions.append(llm_response.state_update.misconception)

        # Move to next question if answer was sufficient
        if is_sufficient:
            state.answered_question_ids.append(state.question_ids[state.question_index])
            state.question_index += 1

        return state

    def _build_prompt(self, state: ConversationState, user_input: str, is_json_mode: bool = True) -> str:
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

        summary = f"You're tutoring a student who's answered {total_questions} questions ({correct_answers} correct)."

        if state.hints_given > 0:
            summary += f" You've provided hints on {state.hints_given} of those questions."

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

    async def _save_state(self, user_id: str, session_id: str, state: ConversationState):
        await self.redis_manager.store_conversation_state(user_id, session_id, state)
