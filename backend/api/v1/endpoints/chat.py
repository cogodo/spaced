from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from core.services.session_service import SessionService
from core.services.topic_service import TopicService
from core.services.question_service import QuestionService
from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger

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


@router.get("/popular-topics")
async def get_popular_topics(
    limit: int = 6,
    current_user: dict = Depends(get_current_user)
) -> PopularTopicsResponse:
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
    request: ValidateTopicsRequest,
    current_user: dict = Depends(get_current_user)
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
    request: StartSessionRequest,
    current_user: dict = Depends(get_current_user)
) -> StartSessionResponse:
    """Start a chat-compatible learning session"""
    try:
        topic_service = TopicService()
        session_service = SessionService()
        question_service = QuestionService()
        
        logger.info("Starting chat session for user %s with topics: %s", current_user['uid'], request.topics)
        
        # 1. Find or create topics
        topics = await topic_service.find_or_create_topics(
            request.topics, 
            current_user["uid"]
        )
        
        if not topics:
            raise HTTPException(400, "No valid topics provided")
        
        # 2. Select primary topic for session (for now, use the first one)
        primary_topic = topics[0]
        
        # 3. Ensure the topic has questions
        questions = await question_service.get_topic_questions(primary_topic.id, current_user["uid"])
        if not questions:
            # Generate a small initial set of questions quickly (5 instead of 20)
            logger.info("No questions found for topic %s, generating initial question set...", primary_topic.name)
            try:
                questions = await question_service.generate_initial_questions(primary_topic, current_user["uid"])
                if questions:
                    await topic_service.update_question_bank(
                        primary_topic.id, 
                        current_user["uid"],
                        [q.id for q in questions]
                    )
                    logger.info("Generated %d initial questions for topic %s", len(questions), primary_topic.name)
                else:
                    safe_topic_name = primary_topic.name.replace("{", "{{").replace("}", "}}")
                    raise HTTPException(500, f"Failed to generate questions for topic: {safe_topic_name}")
            except Exception as e:
                logger.error("Error generating questions for topic %s", primary_topic.name, extra={"error_detail": str(e)})
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
            session_id=request.session_id  # Use provided session ID if available
        )
        
        # 5. Get first question
        _, question = await session_service.get_current_question(session.id, current_user["uid"])
        
        if not question:
            raise HTTPException(500, "Failed to get first question")
        
        # 6. Format response for chat
        response = StartSessionResponse(
            session_id=session.id,
            message=f"Let's learn about {primary_topic.name}!\n\n**Question 1:**\n{question.text}",
            next_question=question.text,
            topics=[t.name for t in topics]
        )
        
        logger.info("Successfully started chat session %s for user %s", session.id, current_user['uid'])
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting chat session", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to start session: {safe_error_message}")


@router.post("/answer", response_model=AnswerResponse)
async def submit_chat_answer(
    request: AnswerRequest,
    current_user: dict = Depends(get_current_user)
) -> AnswerResponse:
    """Submit answer in chat format"""
    try:
        session_service = SessionService()
        
        logger.info("Processing answer for session %s by user %s", request.session_id, current_user['uid'])
        
        # 1. Verify session belongs to user
        session = await session_service.get_session(request.session_id, current_user["uid"])
        if not session:
            raise HTTPException(404, "Session not found")
        
        if session.userUid != current_user["uid"]:
            raise HTTPException(403, "Access denied")
        
        # 2. Submit answer to session
        result = await session_service.submit_response(
            request.session_id, 
            current_user["uid"],
            request.user_input
        )
        
        # 3. Format response for chat
        if result["isComplete"]:
            # Current session completed (5 questions)
            session_score = result.get("finalScore", 0)
            session_questions = result.get("totalQuestions", 5)
            topic_progress = result.get("topicProgress", 0)
            total_topic_questions = result.get("totalTopicQuestions", 20)
            is_topic_complete = result.get("topicComplete", False)
            
            # Calculate actual answered questions (excluding skipped ones) for this session
            session_data = await session_service.get_session(request.session_id, current_user["uid"])
            if session_data and session_data.currentSessionQuestionCount > 0:
                messages = await session_service.get_session_messages(request.session_id, current_user["uid"])
                current_session_messages = messages[-session_data.currentSessionQuestionCount:] if len(messages) >= session_data.currentSessionQuestionCount else messages
                questions_answered = len([m for m in current_session_messages if m.answerText.strip() != ""])
            else:
                questions_answered = 0
            
            # Calculate percentage score for display
            percentage_score = int(session_score * 20) if session_score <= 5 else int(session_score)
            
            if is_topic_complete:
                # All 20 questions in topic completed
                overall_score = result.get("overallTopicScore", session_score)
                overall_percentage = int(overall_score * 20) if overall_score <= 5 else int(overall_score)
                fsrs_info = result.get("fsrs", {})
                
                # Build completion message with FSRS info
                completion_message = (
                    f"🎉 **Topic Mastery Achieved!**\n\n"
                    f"📊 **Final Session Results:**\n"
                    f"• Questions Answered: {questions_answered}/{session_questions}\n"
                    f"• Session Score: {session_score:.1f}/{questions_answered} ({int((session_score * questions_answered) / max(questions_answered, 1) * 100)}%)\n\n"
                    f"🏆 **Overall Topic Performance:**\n"
                    f"• Topic Average: {overall_score:.1f}/5.0 ({overall_percentage}%)\n\n"
                )
                
                # Add FSRS scheduling information
                if fsrs_info:
                    days_until_review = fsrs_info.get("daysUntilReview", 0)
                    if days_until_review > 0:
                        completion_message += (
                            f"📅 **Next Review:** {days_until_review} days\n"
                            f"🧠 **Memory Strength:** {fsrs_info.get('stability', 0):.1f}/5.0\n\n"
                        )
                    else:
                        completion_message += "📅 **Next Review:** Due soon\n\n"
                
                completion_message += "Outstanding! You've demonstrated mastery of this topic. Your progress has been saved for optimal spaced repetition scheduling."
            else:
                # Session complete, but more questions remain in topic
                completion_message = (
                    f"🎉 **Session Complete!**\n\n"
                    f"📊 **Your Results:**\n"
                    f"• Questions Answered: {questions_answered}/{session_questions}\n"
                    f"• Session Score: {session_score:.1f}/{questions_answered} ({int((session_score * questions_answered) / max(questions_answered, 1) * 100)}%)\n\n"
                    f"Great progress! Your learning has been saved and will help optimize your future study sessions.\n\n"
                    f"Ready for another session? Choose a topic to continue your learning journey!"
                )
            
            response_data = AnswerResponse(
                isDone=True,
                scores={"overall": int((session_score * questions_answered) / max(questions_answered, 1) * 100)},
                message=completion_message,
                final_score=session_score,
                questions_answered=questions_answered,
                total_questions=session_questions,
                topic_progress=topic_progress,
                total_topic_questions=total_topic_questions,
                topic_complete=is_topic_complete
            )
        else:
            # Continue with next question
            _, next_question = await session_service.get_current_question(request.session_id, current_user["uid"])
            
            if not next_question:
                raise HTTPException(500, "Failed to get next question")
            
            # Build response message with feedback
            response_message = ""
            if result.get("feedback") and result["feedback"].strip():
                # Escape curly braces in feedback to prevent f-string formatting errors
                safe_feedback = result["feedback"].replace("{", "{{").replace("}", "}}")
                response_message += f"💡 **Feedback:** {safe_feedback}\n\n"
            
            current_question_index = result.get("questionIndex", 1)
            response_message += f"**Question {current_question_index + 1}:**\n{next_question.text}"
            
            response_data = AnswerResponse(
                isDone=False,
                next_question=next_question.text,
                message=response_message,
                feedback=result.get("feedback", ""),
                score=result["score"],
                question_index=current_question_index,
                total_questions=result.get("totalQuestions", 1)
            )
        
        logger.info("Successfully processed answer for session %s", request.session_id)
        return response_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing answer for session %s", request.session_id, extra={"error_detail": str(e)})
        # Escape curly braces in exception message to prevent f-string formatting errors
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to process answer: {safe_error_message}")


@router.get("/search-topics")
async def search_topics(
    q: str,
    current_user: dict = Depends(get_current_user)
):
    """Search user's topics with fuzzy matching"""
    try:
        topic_service = TopicService()
        topics = await topic_service.search_topics(q, current_user["uid"])
        
        return {
            "query": q,
            "topics": [{"name": t.name, "description": t.description, "id": t.id} for t in topics]
        }
        
    except Exception as e:
        logger.error("Error searching topics", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to search topics: {safe_error_message}")


@router.get("/session/{session_id}/status")
async def get_session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
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
            "started_at": session.startedAt.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting session status", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to get session status: {safe_error_message}") 