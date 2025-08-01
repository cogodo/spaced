from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from app.config import settings
from core.models.conversation import (
    ConversationState,
    LLMResponse,
    Turn,
)
from core.models.llm_outputs import NextAction
from core.models.session import Session, SessionState, TurnState
from core.monitoring.logger import get_logger
from core.repositories.question_repository import QuestionRepository
from core.repositories.topic_repository import TopicRepository
from core.services.clarification_service import ClarificationService
from core.services.evaluation_service import EvaluationError, EvaluationService
from core.services.feedback_service import FeedbackError, FeedbackService
from core.services.question_service import QuestionService
from core.services.routing_service import RoutingService
from core.services.session_service import SessionService

# from infrastructure.redis.session_manager import RedisSessionManager  # Commented out Redis

logger = get_logger(__name__)


class ConversationServiceError(Exception):
    """Base exception for ConversationService errors."""

    pass


# --- LLM Interaction Models ---


class ConversationService:
    """
    Manages the one-question-per-call conversation flow.
    """

    def __init__(self):
        # self.redis_manager = RedisSessionManager()  # Commented out Redis
        self.question_service = QuestionService()
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.topic_repo = TopicRepository()
        self.question_repo = QuestionRepository()
        self.session_service = SessionService()
        self.evaluation_service = EvaluationService()
        self.feedback_service = FeedbackService()
        self.routing_service = RoutingService()
        self.clarification_service = ClarificationService()

    async def process_turn(self, chat_id: str, user_uid: str, user_input: str) -> str:
        """
        Processes a single turn of the conversation, managing state and returning
        the next bot message.
        """
        try:
            logger.info(f"Processing turn for chat {chat_id}")
            session = self.session_service.get_session(chat_id, user_uid)
            if not session:
                raise ValueError("Chat session not found.")

            # Check if session is already completed
            if session.state == SessionState.COMPLETED or session.isCompleted:
                return "This session has already been completed. You can start a new session to continue learning!"

            # Handle direct actions (skip/end) before state machine logic
            user_input_lower = user_input.lower().strip()
            if user_input_lower in ["skip", "skip question", "skip this question"]:
                return await self._handle_skip_question(session)
            elif user_input_lower in ["end", "end session", "end chat", "quit", "stop"]:
                summary = await self.end_session(session)
                return f"Session ended! Here's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

            # Main state machine logic
            if session.turnState == TurnState.AWAITING_INITIAL_ANSWER:
                return await self._handle_initial_answer(session, user_input)
            elif session.turnState == TurnState.AWAITING_FOLLOW_UP:
                return await self._handle_follow_up(session, user_input)
            elif session.turnState == TurnState.AWAITING_NEXT_ACTION:
                return await self._handle_next_action(session, user_input)
            else:
                raise ValueError(f"Invalid turn state: {session.turnState}")
        except (EvaluationError, FeedbackError) as e:
            # Catch specific, known errors and log them.
            # These are errors that are part of the expected "unhappy path"
            logger.error(f"A service error occurred during turn processing for chat {chat_id}: {e}", exc_info=True)
            # We can raise a specific error that the endpoint can then handle
            raise ConversationServiceError(f"Failed to process turn: {e}") from e
        except Exception as e:
            # Catch any other, unexpected errors.
            logger.error(f"An unexpected error occurred processing turn for chat {chat_id}", exc_info=True)
            # Re-raise a generic error to be handled by the endpoint
            raise ConversationServiceError("An unexpected internal error occurred.") from e

    async def _handle_initial_answer(self, session: Session, user_input: str) -> str:
        """Handles the user's first answer to a question."""
        _, question = self.session_service.get_current_question(session.id, session.userUid)
        if not question:
            # End session if we run out of questions
            summary = await self.end_session(session)
            return f"It looks like we've run out of questions! Here's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

        try:
            score = await self.evaluation_service.score_answer(question, user_input, after_hint=False)
            feedback = await self.feedback_service.generate_feedback(question, user_input, score)

            if score.score >= 4:
                # Good answer, move to next question prompt
                session.scores[question.id] = score.score
                session.turnState = TurnState.AWAITING_NEXT_ACTION
                self.session_service.repository.update(session.id, session.userUid, session.dict())

                # Check if we've answered 5 questions
                answered_questions = len(session.scores)
                if answered_questions >= 5:
                    summary = await self.end_session(session)
                    return f"{feedback}\n\nSession completed! You've answered 5 questions.\n\nHere's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

                return f"{feedback}\n\nReady for the next question, or do you have any questions about this one?"
            else:
                # Poor answer, await follow-up
                session.initialScore = score.score
                session.turnState = TurnState.AWAITING_FOLLOW_UP
                self.session_service.repository.update(session.id, session.userUid, session.dict())
                return feedback

        except ValueError as e:
            logger.error(f"Error processing initial answer: {str(e)}")
            return f"I'm having trouble processing your answer right now. {str(e)}"

    async def _handle_follow_up(self, session: Session, user_input: str) -> str:
        """Handles the user's response after receiving a hint."""
        _, question = self.session_service.get_current_question(session.id, session.userUid)
        if not question:
            # End session if we run out of questions
            summary = await self.end_session(session)
            return f"Error: Could not find the current question. Here's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

        try:
            # Re-evaluate the answer, this time noting it's after a hint
            second_score = await self.evaluation_service.score_answer(question, user_input, after_hint=True)

            # Average the scores
            final_score = round((session.initialScore + second_score.score) / 2)
            session.scores[question.id] = final_score
            session.turnState = TurnState.AWAITING_NEXT_ACTION

            self.session_service.repository.update(session.id, session.userUid, session.dict())

            # Check if we've answered 5 questions
            answered_questions = len(session.scores)
            if answered_questions >= 5:
                summary = await self.end_session(session)
                return f"Thanks for the clarification! I've recorded a score of {final_score} for that question.\n\nSession completed! You've answered 5 questions.\n\nHere's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

            return f"Thanks for the clarification! I've recorded a score of {final_score} for that question. Ready for the next one?"

        except ValueError as e:
            logger.error(f"Error processing follow-up answer: {str(e)}")
            return f"I'm having trouble processing your follow-up answer right now. {str(e)}"

    async def _handle_next_action(self, session: Session, user_input: str) -> str:
        """Handles the user's response when prompted for the next action."""
        try:
            decision = await self.routing_service.determine_next_action(user_input)

            if decision.next_action == NextAction.MOVE_TO_NEXT_QUESTION:
                session.questionIdx += 1
                session.initialScore = None
                session.turnState = TurnState.AWAITING_INITIAL_ANSWER
                self.session_service.repository.update(session.id, session.userUid, session.dict())

                # Check if we've answered 5 questions (excluding skipped ones)
                answered_questions = len(session.scores)
                if answered_questions >= 5:
                    summary = await self.end_session(session)
                    return f"Session completed! You've answered 5 questions.\n\nHere's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

                _, next_question = self.session_service.get_current_question(session.id, session.userUid)
                if not next_question:
                    # End session if we run out of questions before reaching 5
                    summary = await self.end_session(session)
                    return f"You've completed all the questions! Here's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"
                return f"Great, let's move on. Here is your next question:\n\n{next_question.text}"

            elif decision.next_action == NextAction.END_CHAT:
                summary = await self.end_session(session)
                return f"Session ended! Here's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

            elif decision.next_action == NextAction.AWAIT_CLARIFICATION:
                _, question = self.session_service.get_current_question(session.id, session.userUid)
                if not question:
                    # End session if we run out of questions
                    summary = await self.end_session(session)
                    return f"Error: Could not find the current question. Here's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

                try:
                    answer, impact = await self.clarification_service.handle_clarification(question, user_input)

                    # If the clarification was very helpful, penalize score and move on
                    if impact.adjusted_score == 1:
                        session.scores[question.id] = 1
                        session.turnState = TurnState.AWAITING_NEXT_ACTION
                        self.session_service.repository.update(session.id, session.userUid, session.dict())

                        # Check if we've answered 5 questions
                        answered_questions = len(session.scores)
                        if answered_questions >= 5:
                            summary = await self.end_session(session)
                            return f"{answer}\n\nSince that explanation was very direct, I've marked this question as needing more review later.\n\nSession completed! You've answered 5 questions.\n\nHere's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

                        return f"{answer}\n\nSince that explanation was very direct, I've marked this question as needing more review later. Ready for the next question?"
                    else:
                        # Otherwise, just provide the info and wait for another attempt
                        return f"{answer}\n\nDoes that help clarify things? Feel free to try answering the original question again."

                except ValueError as e:
                    logger.error(f"Error handling clarification: {str(e)}")
                    return f"I'm having trouble providing clarification right now. {str(e)}"

        except ValueError as e:
            logger.error(f"Error determining next action: {str(e)}")
            return f"I'm having trouble understanding your response right now. {str(e)}"

    async def _handle_skip_question(self, session: Session) -> str:
        """Handles skipping the current question and moving to the next one."""
        try:
            # Get current question to mark it as skipped
            _, current_question = self.session_service.get_current_question(session.id, session.userUid)
            if not current_question:
                # End session if we run out of questions
                summary = await self.end_session(session)
                return f"You've completed all the questions! Here's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

            # Skip the question without recording a score (exclude from scoring)
            session.questionIdx += 1
            session.initialScore = None
            session.turnState = TurnState.AWAITING_INITIAL_ANSWER

            # Save the updated session
            self.session_service.repository.update(session.id, session.userUid, session.dict())

            # Check if we've answered 5 questions (excluding skipped ones)
            answered_questions = len(session.scores)
            if answered_questions >= 5:
                summary = await self.end_session(session)
                return f"Session completed! You've answered 5 questions.\n\nHere's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

            # Get the next question
            _, next_question = self.session_service.get_current_question(session.id, session.userUid)
            if not next_question:
                # End session if we run out of questions before reaching 5
                summary = await self.end_session(session)
                return f"You've completed all the questions! Here's your summary:\nQuestions Answered: {summary['questions_answered']}\nAverage Score: {summary['average_score']:.2f}\n\n{summary['message']}"

            return f"Question skipped. Here's your next question:\n\n{next_question.text}"

        except Exception as e:
            logger.error(f"Error skipping question: {str(e)}")
            return f"I'm having trouble skipping the question right now. {str(e)}"

    async def skip_question(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Skips the current question, updates the state, and returns the next question.
        """
        # state = await self.redis_manager.get_conversation_state(user_id, session_id) # Commented out Redis
        # if not state: # Commented out Redis
        #     raise ValueError("Conversation state not found.") # Commented out Redis

        # Mark current question as answered (skipped) # Commented out Redis
        # state.answered_question_ids.append(state.question_ids[state.question_index]) # Commented out Redis
        # state.question_index += 1 # Commented out Redis
        # state.history.append(Turn(user_input="skip", bot_response="Question skipped.")) # Commented out Redis

        # Save the updated state # Commented out Redis
        # await self._save_state(user_id, session_id, state) # Commented out Redis

        # Check for completion # Commented out Redis
        # if state.question_index >= len(state.question_ids): # Commented out Redis
        #     return { # Commented out Redis
        #         "is_done": True, # Commented out Redis
        #         "next_question": "Congratulations, you've completed all questions for this topic!", # Commented out Redis
        #     } # Commented out Redis

        # Get the next question # Commented out Redis
        # next_question = await self.question_repo.get_by_id( # Commented out Redis
        #     user_id=user_id, # Commented out Redis
        #     topic_id=state.topic_id, # Commented out Redis
        #     question_id=state.question_ids[state.question_index], # Commented out Redis
        # ) # Commented out Redis

        # return {"is_done": False, "next_question": next_question.text} # Commented out Redis
        raise NotImplementedError("Redis session management is currently disabled.")

    async def end_session(self, session: Session) -> Dict[str, Any]:
        """
        Ends the session, calculates analytics, updates FSRS, and returns a summary.
        """
        logger.info(f"Ending session for chat {session.id}")
        session.end_session()
        self.session_service.repository.update(session.id, session.userUid, session.dict())

        # Calculate stats
        questions_answered = len(session.scores)
        if questions_answered == 0:
            average_score = 0
        else:
            average_score = sum(session.scores.values()) / questions_answered

        # Get topic name for the motivational message
        topic_name = "your recent topic"
        try:
            if session.topicId and session.userUid:
                topic = self.topic_repo.get_by_id(session.topicId, session.userUid)
                if topic:
                    topic_name = topic.name
        except Exception as e:
            logger.warning(f"Could not retrieve topic name for chat {session.id}: {e}")

        # Generate motivational message
        motivational_message = await self._generate_summary_message(average_score, questions_answered, topic_name)

        # Update FSRS
        if questions_answered > 0:
            try:
                from core.services.fsrs_service import FSRSService

                fsrs_service = FSRSService()
                fsrs_service.update_fsrs_for_topic(session.userUid, session.topicId, session.scores)
                logger.info(f"Successfully updated FSRS for topic {session.topicId}")
            except Exception as e:
                logger.error(f"Failed to update FSRS for topic {session.topicId}: {e}", exc_info=True)
                # Don't fail the whole session end if FSRS update fails

        # Create summary
        summary = {
            "questions_answered": questions_answered,
            "average_score": average_score,
            "message": motivational_message,
        }

        return summary

    async def _generate_summary_message(self, average_score: float, questions_answered: int, topic_name: str) -> str:
        """Generates a short, motivational summary message based on session performance."""
        if questions_answered == 0:
            return "No questions were answered in this session, but keep at it!"

        prompt = f"""
        Generate a short, motivational, and friendly message for a user who just finished a learning session on the topic "{topic_name}".

        Their performance:
        - Questions answered: {questions_answered}
        - Average score: {average_score:.2f} out of 5

        The message should be encouraging. If the score is low, motivate them to keep practicing. If the score is high, congratulate them. The tone should be like a friendly tutor. It must be concise (1-2 sentences).
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are Spaced, a friendly and motivational learning tutor."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.5,
            )
            content = response.choices[0].message.content
            return content.strip() if content else "Great job! Keep up the consistent practice."
        except Exception as e:
            logger.error(f"Error generating summary message: {e}", exc_info=True)
            return "Great job! Keep up the consistent practice."

    async def get_or_create_state(
        self, user_id: str, session_id: str, topic_id: Optional[str] = None
    ) -> ConversationState:
        """Creates a new conversation state for the user's session."""
        if topic_id is None:
            raise ValueError("Topic ID is required for conversation state creation.")
        questions = self.question_service.get_topic_questions(topic_id, user_id)
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
        """Helper to call the LLM and return the text content."""
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,  # Explicitly set a higher token limit
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM returned empty content.")
            return content
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            raise ConversationServiceError("Failed to get a response from the AI.") from e

    async def _save_state(self, user_id: str, session_id: str, state: ConversationState):
        # await self.redis_manager.save_conversation_state(user_id, session_id, state) # Commented out Redis
        raise NotImplementedError("Redis session management is currently disabled.")
