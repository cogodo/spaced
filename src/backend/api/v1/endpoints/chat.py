from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger
from core.services.conversation_service import ConversationService
from core.services.question_service import QuestionService
from core.services.session_service import SessionService
from core.services.topic_service import TopicService

logger = get_logger("chat_api")
router = APIRouter(tags=["chat"])


class StartSessionRequest(BaseModel):
    topics: List[str]
    session_type: str = "custom_topics"
    max_topics: int = 3
    max_questions: int = 7
    session_id: Optional[str] = None  # Allow frontend to specify session ID


class AnswerRequest(BaseModel):
    session_id: str
    user_input: str


class PopularTopicsResponse(BaseModel):
    topics: List[Dict[str, str]]


class ValidateTopicsRequest(BaseModel):
    topics: List[str]


class ValidateTopicsResponse(BaseModel):
    valid_topics: List[str]
    suggestions: List[Dict[str, Any]]
    has_errors: bool


class StartSessionResponse(BaseModel):
    session_id: str
    message: str
    next_question: str
    topics: List[str]
    topic_id: str


class AnswerResponse(BaseModel):
    isDone: bool
    next_question: Optional[str] = None
    message: Optional[str] = None
    feedback: Optional[str] = None
    score: Optional[int] = None
    question_index: Optional[int] = None
    total_questions: Optional[int] = None
    scores: Optional[Dict[str, int]] = None
    final_score: Optional[float] = None
    questions_answered: Optional[int] = None
    topic_progress: Optional[int] = None
    total_topic_questions: Optional[int] = None
    topic_complete: Optional[bool] = None


class ConversationTurnRequest(BaseModel):
    session_id: str
    topic_id: str
    user_input: str


class EndConversationRequest(BaseModel):
    session_id: str


class ConversationTurnResponse(BaseModel):
    bot_response: str


class EndConversationResponse(BaseModel):
    final_score: float
    questions_answered: int
    total_questions: int
    percentage_score: int


@router.get("/popular-topics")
async def get_popular_topics(limit: int = 6, current_user: dict = Depends(get_current_user)) -> PopularTopicsResponse:
    """Get popular topics for quick-pick menu"""
    try:
        topic_service = TopicService()
        topics = await topic_service.get_popular_topics(limit)

        return PopularTopicsResponse(topics=topics)

    except Exception as e:
        logger.error("Error getting popular topics", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to get popular topics: {safe_error_message}")


@router.post("/validate-topics")
async def validate_topics(
    request: ValidateTopicsRequest, current_user: dict = Depends(get_current_user)
) -> ValidateTopicsResponse:
    """Validate topic names and provide suggestions"""
    try:
        topic_service = TopicService()
        result = await topic_service.validate_topics(request.topics, current_user["uid"])

        return ValidateTopicsResponse(**result)

    except Exception as e:
        logger.error("Error validating topics", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to validate topics: {safe_error_message}")


@router.post("/start_session", response_model=StartSessionResponse)
async def start_chat_session(
    request: StartSessionRequest, current_user: dict = Depends(get_current_user)
) -> StartSessionResponse:
    """Start a chat-compatible learning session"""
    try:
        topic_service = TopicService()
        session_service = SessionService()
        question_service = QuestionService()

        logger.info(
            "Starting chat session for user %s with topics: %s",
            current_user["uid"],
            request.topics,
        )

        # 1. Find or create topics
        topics = await topic_service.find_or_create_topics(request.topics, current_user["uid"])

        if not topics:
            raise HTTPException(400, "No valid topics provided")

        # 2. Select primary topic for session (for now, use the first one)
        primary_topic = topics[0]

        # 3. Ensure the topic has questions
        questions = await question_service.get_topic_questions(primary_topic.id, current_user["uid"])
        if not questions:
            # Generate a small initial set of questions quickly (5 instead of 20)
            logger.info(
                "No questions found for topic %s, generating initial question set...",
                primary_topic.name,
            )
            try:
                questions = await question_service.generate_initial_questions(primary_topic, current_user["uid"])
                if questions:
                    await topic_service.update_question_bank(
                        primary_topic.id, current_user["uid"], [q.id for q in questions]
                    )
                    logger.info(
                        "Generated %d initial questions for topic %s",
                        len(questions),
                        primary_topic.name,
                    )
                else:
                    safe_topic_name = primary_topic.name.replace("{", "{{").replace("}", "}}")
                    raise HTTPException(
                        500,
                        f"Failed to generate questions for topic: {safe_topic_name}",
                    )
            except Exception as e:
                logger.error(
                    "Error generating questions for topic %s",
                    primary_topic.name,
                    extra={"error_detail": str(e)},
                )
                safe_topic_name = primary_topic.name.replace("{", "{{").replace("}", "}}")
                raise HTTPException(500, f"Failed to generate questions for topic: {safe_topic_name}")

        # Ensure we have at least one question to start the session
        if not questions:
            safe_topic_name = primary_topic.name.replace("{", "{{").replace("}", "}}")
            raise HTTPException(500, f"No questions available for topic: {safe_topic_name}")

        # 4. Start learning session
        session = await session_service.start_session(
            user_uid=current_user["uid"],
            topic_id=primary_topic.id,
            session_id=request.session_id,  # Use provided session ID if available
        )

        # 5. Get first question
        _, question = await session_service.get_current_question(session.id, current_user["uid"])

        if not question:
            raise HTTPException(500, "Failed to get first question")

        # 6. Format response for chat
        response = StartSessionResponse(
            session_id=session.id,
            message=(f"Let's learn about {primary_topic.name}!\n\n**Question 1:**\n{question.text}"),
            next_question=question.text,
            topics=[t.name for t in topics],
            topic_id=primary_topic.id,
        )

        logger.info(
            "Successfully started chat session %s for user %s",
            session.id,
            current_user["uid"],
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting chat session", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to start session: {safe_error_message}")


@router.post("/conversation/turn", response_model=ConversationTurnResponse)
async def handle_conversation_turn(request: ConversationTurnRequest, current_user: dict = Depends(get_current_user)):
    """Handles one turn of a conversation using the new stateless architecture."""
    try:
        conversation_service = ConversationService()
        user_id = current_user["uid"]

        bot_response = await conversation_service.handle_turn(
            user_id=user_id,
            session_id=request.session_id,
            topic_id=request.topic_id,
            user_input=request.user_input,
        )

        return ConversationTurnResponse(bot_response=bot_response)

    except Exception as e:
        logger.error(
            "Error handling conversation turn for session %s",
            request.session_id,
            extra={"error_detail": str(e)},
        )
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to handle conversation turn: {safe_error_message}")


@router.post("/conversation/end", response_model=EndConversationResponse)
async def end_conversation(request: EndConversationRequest, current_user: dict = Depends(get_current_user)):
    """Ends a conversation and returns final analytics."""
    try:
        conversation_service = ConversationService()
        user_id = current_user["uid"]

        analytics = await conversation_service.end_session(user_id=user_id, session_id=request.session_id)

        return EndConversationResponse(**analytics)

    except Exception as e:
        logger.error(
            "Error ending conversation for session %s",
            request.session_id,
            extra={"error_detail": str(e)},
        )
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to end conversation: {safe_error_message}")


@router.get("/search-topics")
async def search_topics(q: str, current_user: dict = Depends(get_current_user)):
    """Search user's topics with fuzzy matching"""
    try:
        topic_service = TopicService()
        topics = await topic_service.search_topics(q, current_user["uid"])

        return {
            "query": q,
            "topics": [{"name": t.name, "description": t.description, "id": t.id} for t in topics],
        }

    except Exception as e:
        logger.error("Error searching topics", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to search topics: {safe_error_message}")


@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get current session status for chat interface"""
    try:
        session_service = SessionService()

        # Get session and verify ownership
        session = await session_service.get_session(session_id, current_user["uid"])
        if not session:
            raise HTTPException(404, "Session not found")

        if session.userUid != current_user["uid"]:
            raise HTTPException(403, "Access denied")

        # Get current question if session is active
        _, current_question = await session_service.get_current_question(session_id, current_user["uid"])

        # Get message count for accurate responses count
        messages = await session_service.get_session_messages(session_id, current_user["uid"])

        is_complete = current_question is None

        return {
            "session_id": session_id,
            "is_complete": is_complete,
            "question_index": session.questionIndex,
            "total_questions": len(session.questionIds),
            "responses_count": len(messages),
            "current_question": current_question.text if current_question else None,
            "started_at": session.startedAt.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting session status", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to get session status: {safe_error_message}")
