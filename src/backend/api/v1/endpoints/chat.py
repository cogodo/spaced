from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger
from core.services.context_service import ContextService
from core.services.conversation_service import ConversationService
from core.services.question_service import QuestionService
from core.services.topic_service import TopicService

logger = get_logger("chat_api")
router = APIRouter(tags=["chat"])


class StartChatRequest(BaseModel):
    topics: List[str]
    chat_id: Optional[str] = None  # Allow frontend to specify chat ID


class StartChatResponse(BaseModel):
    chat_id: str
    message: str
    next_question: str
    topics: List[str]
    topic_id: str


class TurnRequest(BaseModel):
    user_input: str


class TurnResponse(BaseModel):
    bot_response: str


@router.post("/start", response_model=StartChatResponse)
async def start_chat(request: StartChatRequest, current_user: dict = Depends(get_current_user)) -> StartChatResponse:
    """Start a chat-based learning session."""
    try:
        topic_service = TopicService()
        context_service = ContextService()
        user_uid = current_user["uid"]

        logger.info(f"Starting chat for user {user_uid} with topics: {request.topics}")

        topics = await topic_service.find_or_create_topics(request.topics, user_uid)
        if not topics:
            raise HTTPException(400, "No valid topics provided")

        primary_topic = topics[0]
        question_service = QuestionService()
        questions = await question_service.get_topic_questions(primary_topic.id, user_uid)

        if not questions:
            logger.info(f"Generating initial questions for topic {primary_topic.name}...")
            questions = await question_service.generate_initial_questions(primary_topic, user_uid)
            if not questions:
                raise HTTPException(500, f"Failed to generate questions for topic: {primary_topic.name}")
            await topic_service.update_question_bank(primary_topic.id, user_uid, [q.id for q in questions])

        context = await context_service.start_context(
            user_uid=user_uid,
            topic_id=primary_topic.id,
            context_id=request.chat_id,
        )

        _, question = await context_service.get_current_question(context.chatId, user_uid)
        if not question:
            raise HTTPException(500, "Failed to get first question")

        response = StartChatResponse(
            chat_id=context.chatId,
            message=f"Let's learn about {primary_topic.name}!\n\n**Question 1:**\n{question.text}",
            next_question=question.text,
            topics=[t.name for t in topics],
            topic_id=primary_topic.id,
        )

        logger.info(f"Successfully started chat {context.chatId} for user {user_uid}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting chat session", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to start chat: {safe_error_message}")


@router.post("/{chat_id}/turn", response_model=TurnResponse)
async def handle_turn(
    chat_id: str, request: TurnRequest, current_user: dict = Depends(get_current_user)
) -> TurnResponse:
    """Handles a single turn in the conversation."""
    try:
        conversation_service = ConversationService()
        user_uid = current_user["uid"]
        bot_response = await conversation_service.process_turn(chat_id, user_uid, request.user_input)
        return TurnResponse(bot_response=bot_response)
    except ValueError as e:
        logger.warning(f"Value error in chat turn for {chat_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error handling turn for chat {chat_id}", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to handle turn: {safe_error_message}")
