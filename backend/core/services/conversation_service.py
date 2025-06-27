import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from app.config import settings

from core.services.question_service import QuestionService
from infrastructure.redis.session_manager import RedisSessionManager
from core.models import Question
from core.models.conversation import ConversationState, LLMStateUpdate, LLMResponse

# --- LLM Interaction Models ---

class ConversationService:
    """
    Manages the one-question-per-call conversation flow.
    """
    def __init__(self):
        self.redis_manager = RedisSessionManager()
        self.question_service = QuestionService()
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def handle_turn(self, user_id: str, session_id: str, topic_id: str, user_input: str) -> str:
        """
        Handles a single turn in the conversation.
        """
        state = await self.redis_manager.get_conversation_state(user_id, session_id)
        
        if not state:
            state = await self._initialize_state(user_id, topic_id)

        current_question, next_question = await self._get_next_questions(state, user_id, topic_id)

        if not current_question:
            return "You have completed all questions for this topic! Great job."

        prompt = self._build_prompt(state, current_question, user_input, next_question)
        
        try:
            llm_response_str = await self._call_llm(prompt)
            llm_response = LLMResponse.model_validate_json(llm_response_str)
            
            response_text = llm_response.user_facing_response
            
            # The LLM decides if we should move to the next question by including a token.
            if "[NEXT_QUESTION]" in response_text:
                state = self._update_state(state, llm_response.state_update, current_question.id)
                
                if next_question:
                    response_text = response_text.replace("[NEXT_QUESTION]", f"\\n\\n**Next Question:**\\n{next_question.text}")
                else:
                    response_text = response_text.replace("[NEXT_QUESTION]", "\\n\\nCongratulations, you've completed all questions for this topic!")
            
            await self.redis_manager.store_conversation_state(user_id, session_id, state)

            return response_text

        except (json.JSONDecodeError, ValueError) as e:
            # Handle cases where LLM output is not valid JSON
            # or other value errors like no questions found.
            print(f"Error processing turn: {e}")
            return "I'm having a bit of trouble with this topic. It seems there are no questions available. Please try another topic."
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "An unexpected error occurred. Please try again later."

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

    async def _initialize_state(self, user_id: str, topic_id: str) -> ConversationState:
        """Creates a new conversation state for the user's session."""
        questions = await self.question_service.get_topic_questions(topic_id, user_id)
        if not questions:
            raise ValueError(f"No questions found for topic ID '{topic_id}'. Cannot start conversation.")
        question_ids = [q.id for q in questions]
        return ConversationState(question_ids=question_ids)

    async def _get_next_questions(self, state: ConversationState, user_id: str, topic_id: str) -> (Optional[Question], Optional[Question]):
        """Determines the next one or two questions to ask."""
        unanswered_ids = [qid for qid in state.question_ids if qid not in state.answered_question_ids]
        
        if not unanswered_ids:
            return None, None
        
        current_question_id = unanswered_ids[0]
        current_question = await self.question_service.get_question(current_question_id, user_id, topic_id)
        
        next_question = None
        if len(unanswered_ids) > 1:
            next_question_id = unanswered_ids[1]
            next_question = await self.question_service.get_question(next_question_id, user_id, topic_id)
            
        return current_question, next_question

    def _update_state(self, state: ConversationState, update: LLMStateUpdate, question_id: str) -> ConversationState:
        """Updates the conversation state based on the LLM response."""
        state.score_history.append(update.score)
        if update.hint_given:
            state.hints_given += 1
        if update.misconception:
            state.misconceptions.append(update.misconception)
        
        state.answered_question_ids.append(question_id)
        state.turn_count += 1
        return state

    def _build_prompt(self, state: ConversationState, question: Question, user_answer: str, next_question: Optional[Question]) -> str:
        """Builds the full prompt for the LLM call."""
        system_blurb = (
            "You are Spaced, a friendly conversational tutor. Your goal is to help students learn by "
            "evaluating their answers and providing feedback. If the answer is sufficient, you must end your response "
            "with the special token [NEXT_QUESTION]. If the answer is incorrect or incomplete, provide hints or ask "
            "follow-up questions to guide the student, but do not include the token."
        )

        state_summary = self._summarize_state(state)
        question_number = len(state.answered_question_ids) + 1

        prompt = f"""
{state_summary}

The student is currently on Question {question_number}.

CURRENT QUESTION: {question.text}
STUDENT'S ANSWER: "{user_answer}"

Your task is to:
1. Evaluate the student's answer for the CURRENT QUESTION.
2. Provide a conversational response that integrates praise or correction.
3. If the student's answer is sufficient, end your response with the exact token: [NEXT_QUESTION]
4. If the student's answer is insufficient, ask a clarifying question or provide a hint about the CURRENT QUESTION. Do NOT include the token.

Return your entire response as a single JSON object with two keys:
- "user_facing_response": A string containing your conversational reply to the student. This is where you will include the [NEXT_QUESTION] token if appropriate.
- "state_update": A JSON object with the following keys:
    - "score": An integer score from 0-5 for the student's answer.
    - "hint_given": A boolean, true if you provided a hint.
    - "misconception": A brief string summarizing any misconception you identified, or null if none.
"""
        return prompt
    
    def _summarize_state(self, state: ConversationState) -> str:
        """Creates a one- or two-sentence summary of the user's state."""
        if state.turn_count == 0:
            return "You are tutoring a new student."

        total_questions = state.turn_count
        correct_answers = sum(1 for score in state.score_history if score >= 3)
        
        summary = (
            f"You're tutoring a student who's answered {total_questions} questions ({correct_answers} correct)."
        )

        if state.hints_given > 0:
            summary += f" You have provided {state.hints_given} hints."

        if state.misconceptions:
            last_misconception = state.misconceptions[-1]
            summary += f" The student recently struggled with: '{last_misconception}'."
            
        return summary
    
    async def _call_llm(self, prompt: str) -> str:
        """Calls the OpenAI API and returns the response content."""
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview", # Using a more advanced model for conversational ability
            messages=[
                {"role": "system", "content": "You are Spaced, a friendly conversational tutor who always responds in the specified JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content 