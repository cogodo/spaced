from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger
from core.services.context_service import ContextService, ContextServiceError
from core.services.conversation_service import (
    ConversationService,
    ConversationServiceError,
)
from core.services.question_service import QuestionGenerationError, QuestionService
from core.services.topic_service import TopicService, TopicServiceError

logger = get_logger("chat_api")
router = APIRouter()


class StartChatRequest(BaseModel):
    topics: List[str]
    chat_id: Optional[str] = None  # Allow frontend to specify chat ID


class StartChatResponse(BaseModel):
    chat_id: str
    message: str
    next_question: str
    topics: List[str]
    topic_id: str


# Keep the old endpoint for backward compatibility
class TurnRequest(BaseModel):
    user_input: str


class TurnResponse(BaseModel):
    bot_response: str


@router.post("/chat/start", response_model=StartChatResponse)
async def start_chat(request: StartChatRequest, current_user: dict = Depends(get_current_user)) -> StartChatResponse:
    """Start a chat-based learning session."""
    user_uid = current_user["uid"]
    logger.info(f"Starting chat for user {user_uid} with topics: {request.topics}")

    try:
        topic_service = TopicService()
        context_service = ContextService()
        question_service = QuestionService()

        # 1. Find or create topics
        topics = await topic_service.find_or_create_topics(request.topics, user_uid)
        if not topics:
            raise HTTPException(400, "No valid topics provided")
        primary_topic = topics[0]

        # 2. Ensure topic has questions, generating them if necessary
        questions = await question_service.get_topic_questions(primary_topic.id, user_uid)
        if not questions:
            logger.info(f"Generating initial questions for topic {primary_topic.name}...")
            questions = await question_service.generate_initial_questions(primary_topic, user_uid)
            if not questions:
                raise HTTPException(500, f"Question generation returned no questions for topic: {primary_topic.name}")

            logger.info(f"Updating question bank for topic {primary_topic.id} with {len(questions)} questions.")
            await topic_service.update_question_bank(primary_topic.id, user_uid, [q.id for q in questions])
            logger.info(f"Successfully updated question bank for topic {primary_topic.id}.")

        # 3. Start the context (chat session)
        logger.info(f"Starting context for user {user_uid} and topic {primary_topic.id}.")
        context = await context_service.start_context(
            user_uid=user_uid,
            topic_id=primary_topic.id,
            context_id=request.chat_id,
        )
        logger.info(f"Successfully started context {context.chatId}.")

        # 4. Get the first question
        logger.info(f"Getting current question for chat {context.chatId}.")
        _, question = await context_service.get_current_question(context.chatId, user_uid)
        if not question:
            raise HTTPException(500, "Failed to get first question for the context")
        logger.info(f"Successfully retrieved first question {question.id} for chat {context.chatId}.")

        # 5. Return the successful response
        response = StartChatResponse(
            chat_id=context.chatId,
            message=f"Let's learn about {primary_topic.name}!\n\n**Question 1:**\n{question.text}",
            next_question=question.text,
            topics=[t.name for t in topics],
            topic_id=primary_topic.id,
        )

        logger.info(f"Successfully started chat {context.chatId} for user {user_uid}")
        return response

    except (QuestionGenerationError, TopicServiceError, ContextServiceError) as e:
        # Log the service-specific error. The exc_info argument is removed to prevent the KeyError.
        # FastAPI's default error handling will still capture and log the full traceback.
        logger.error(f"A specific service error occurred during chat start for user {user_uid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        # Re-raise HTTPException directly to avoid being caught by the generic Exception
        raise
    except Exception:
        # Catch any other unexpected errors and log them.
        logger.error(f"An unexpected error occurred during chat start for user {user_uid}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")


# Keep backward compatibility with old endpoint
@router.post("/chat/{chat_id}/messages", response_model=TurnResponse)
async def handle_turn(
    chat_id: str, request: TurnRequest, current_user: dict = Depends(get_current_user)
) -> TurnResponse:
    """Handles a single turn in the conversation."""
    try:
        conversation_service = ConversationService()
        user_uid = current_user["uid"]
        bot_response = await conversation_service.process_turn(chat_id, user_uid, request.user_input)
        return TurnResponse(bot_response=bot_response)
    except ConversationServiceError as e:
        logger.error(f"Conversation error in chat {chat_id} for user {user_uid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error handling turn for chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred while handling turn.")
