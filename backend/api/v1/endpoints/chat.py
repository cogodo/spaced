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
        logger.error("Error getting popular topics: %s", str(e))
        raise HTTPException(500, f"Failed to get popular topics: {str(e)}")


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
        logger.error("Error validating topics: %s", str(e))
        raise HTTPException(500, f"Failed to validate topics: {str(e)}")


@router.post("/start_session")
async def start_chat_session(
    request: StartSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start a chat-compatible learning session"""
    try:
        topic_service = TopicService()
        session_service = SessionService()
        question_service = QuestionService()
        
        logger.info(f"Starting chat session for user {current_user['uid']} with topics: {request.topics}")
        
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
        questions = await question_service.get_topic_questions(primary_topic.id)
        if not questions:
            # Generate questions for the topic if none exist
            logger.info(f"No questions found for topic {primary_topic.name}, generating...")
            try:
                questions = await question_service.generate_question_bank(primary_topic)
                if questions:
                    await topic_service.update_question_bank(
                        primary_topic.id, 
                        [q.id for q in questions]
                    )
                    logger.info(f"Generated {len(questions)} questions for topic {primary_topic.name}")
                else:
                    raise HTTPException(500, f"Failed to generate questions for topic: {primary_topic.name}")
            except Exception as e:
                logger.error("Error generating questions for topic %s: %s", primary_topic.name, str(e))
                raise HTTPException(500, f"Failed to generate questions for topic: {primary_topic.name}")
        
        # 4. Start learning session
        session = await session_service.start_session(
            user_uid=current_user["uid"],
            topic_id=primary_topic.id
        )
        
        # 5. Get first question
        _, question = await session_service.get_current_question(session.id)
        
        if not question:
            raise HTTPException(500, "Failed to get first question")
        
        # 6. Format response for chat
        response_data = {
            "session_id": session.id,
            "message": f"Let's learn about {primary_topic.name}!\n\n**Question 1:**\n{question.text}",
            "next_question": question.text,
            "topics": [t.name for t in topics]
        }
        
        logger.info(f"Successfully started chat session {session.id} for user {current_user['uid']}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting chat session: %s", str(e))
        raise HTTPException(500, f"Failed to start session: {str(e)}")


@router.post("/answer")
async def submit_chat_answer(
    request: AnswerRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit answer in chat format"""
    try:
        session_service = SessionService()
        
        logger.info(f"Processing answer for session {request.session_id} by user {current_user['uid']}")
        
        # 1. Verify session belongs to user
        session = await session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        
        if session.userUid != current_user["uid"]:
            raise HTTPException(403, "Access denied")
        
        # 2. Submit answer to session
        result = await session_service.submit_response(
            request.session_id, 
            request.user_input
        )
        
        # 3. Format response for chat
        if result["isComplete"]:
            # Session completed
            final_score = result.get("finalScore", 0)
            total_questions = result.get("totalQuestions", 1)
            questions_answered = result.get("questionIndex", 0)
            
            # Calculate percentage score for display
            percentage_score = int(final_score * 20) if final_score <= 5 else int(final_score)
            
            completion_message = (
                f"🎉 **Session Complete!**\n\n"
                f"📊 **Your Results:**\n"
                f"• Questions Answered: {questions_answered}/{total_questions}\n"
                f"• Average Score: {final_score:.1f}/5.0\n"
                f"• Percentage: {percentage_score}%\n\n"
                f"Great job! Your progress has been saved and will help optimize your future learning sessions."
            )
            
            response_data = {
                "isDone": True,
                "scores": {"overall": percentage_score},
                "message": completion_message,
                "final_score": final_score,
                "questions_answered": questions_answered,
                "total_questions": total_questions
            }
        else:
            # Continue with next question
            _, next_question = await session_service.get_current_question(request.session_id)
            
            if not next_question:
                raise HTTPException(500, "Failed to get next question")
            
            # Build response message with feedback
            response_message = ""
            if result.get("feedback") and result["feedback"].strip():
                response_message += f"💡 **Feedback:** {result['feedback']}\n\n"
            
            current_question_index = result.get("questionIndex", 1)
            response_message += f"**Question {current_question_index + 1}:**\n{next_question.text}"
            
            response_data = {
                "isDone": False,
                "next_question": next_question.text,
                "message": response_message,
                "feedback": result.get("feedback", ""),
                "score": result["score"],
                "question_index": current_question_index,
                "total_questions": result.get("totalQuestions", 1)
            }
        
        logger.info(f"Successfully processed answer for session {request.session_id}")
        return response_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing answer for session %s: %s", request.session_id, str(e))
        raise HTTPException(500, f"Failed to process answer: {str(e)}")


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
        logger.error("Error searching topics: %s", str(e))
        raise HTTPException(500, f"Failed to search topics: {str(e)}")


@router.get("/session/{session_id}/status")
async def get_session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get current session status for chat interface"""
    try:
        session_service = SessionService()
        
        # Get session and verify ownership
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        
        if session.userUid != current_user["uid"]:
            raise HTTPException(403, "Access denied")
        
        # Get current question if session is active
        _, current_question = await session_service.get_current_question(session_id)
        
        is_complete = current_question is None
        
        return {
            "session_id": session_id,
            "is_complete": is_complete,
            "question_index": session.questionIndex,
            "total_questions": len(session.questionIds),
            "responses_count": len(session.responses),
            "current_question": current_question.text if current_question else None,
            "started_at": session.startedAt.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting session status: %s", str(e))
        raise HTTPException(500, f"Failed to get session status: {str(e)}") 