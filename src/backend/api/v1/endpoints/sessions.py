import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger
from core.services import SessionService

logger = get_logger("sessions_api")
router = APIRouter()


class StartSessionRequest(BaseModel):
    topicId: str
    sessionType: str = "single_topic"
    sessionId: Optional[str] = None  # Allow frontend to specify session ID


class ResponseRequest(BaseModel):
    answer: str


@router.post("/start", response_model=dict)
async def start_session(
    request: StartSessionRequest, current_user: dict = Depends(get_current_user)
):
    """Start a new learning session"""
    session_service = SessionService()

    # Use frontend session ID if provided, otherwise generate new one
    session_id = request.sessionId or str(uuid.uuid4())

    try:
        session = await session_service.start_session(
            user_uid=current_user.get("uid"),
            topic_id=request.topicId,
            session_id=session_id,  # Pass the session ID to use
        )
        return {"sessionId": session.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error starting session", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start session: {safe_error_message}"
        )


@router.get("/{session_id}")
async def get_session(
    session_id: str, current_user: dict = Depends(get_current_user)
) -> dict:
    """Get session details and current question"""
    session_service = SessionService()

    session, question = await session_service.get_current_question(
        session_id, current_user.get("uid")
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify user owns this session
    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")

    result = {
        "session": session.dict(),
        "currentQuestion": question.dict() if question else None,
        "isComplete": question is None,
    }

    return result


@router.post("/{session_id}/respond")
async def respond_to_question(
    session_id: str,
    request: ResponseRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user),
):
    """Submit response to current question"""
    session_service = SessionService()

    # Verify session exists and user owns it
    session = await session_service.get_session(session_id, current_user.get("uid"))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        result = await session_service.submit_response(
            session_id, current_user.get("uid"), request.answer
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error submitting response", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit response: {safe_error_message}"
        )


@router.post("/{session_id}/skip")
async def skip_question(
    session_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user),
):
    """Skip current question"""
    session_service = SessionService()

    # Verify session exists and user owns it
    session = await session_service.get_session(session_id, current_user.get("uid"))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        result = await session_service.skip_question(
            session_id, current_user.get("uid")
        )

        # Format response for frontend compatibility (similar to chat API)
        if result["isComplete"]:
            # Current session completed (5 questions)
            session_score = result.get("finalScore", 0)
            session_questions = result.get("totalQuestions", 5)
            topic_progress = result.get("topicProgress", 0)
            total_topic_questions = result.get("totalTopicQuestions", 20)
            is_topic_complete = result.get("topicComplete", False)

            # Calculate actual answered questions (excluding skipped ones) for this
            # session
            session = await session_service.get_session(
                session_id, current_user.get("uid")
            )
            messages = await session_service.get_session_messages(
                session_id, current_user.get("uid")
            )
            current_session_messages = (
                messages[-session.currentSessionQuestionCount :]
                if len(messages) >= session.currentSessionQuestionCount
                else messages
            )
            questions_answered = len(
                [m for m in current_session_messages if m.answerText.strip() != ""]
            )

            # Calculate percentage score for display
            score_percentage = int(
                (session_score * questions_answered) / max(questions_answered, 1) * 100
            )

            if is_topic_complete:
                # All 20 questions in topic completed
                overall_score = result.get("overallTopicScore", session_score)
                overall_percentage = (
                    int(overall_score * 20)
                    if overall_score <= 5
                    else int(overall_score)
                )
                completion_message = (
                    f"🎉 **All done!**\n\n"
                    f"📊 **Final Session Results:**\n"
                    f"• Questions Answered: {questions_answered}\n"
                    f"• Session Score: {session_score:.1f}/{questions_answered} "
                    f"({score_percentage}%)\n\n"
                    f"🏆 **Overall Topic Performance:**\n"
                    f"• Topic Average: {overall_score:.1f}/5.0 "
                    f"({overall_percentage}%)\n\n"
                    f"Outstanding! You've demonstrated mastery of this topic. "
                    f"Your progress has been saved for optimal spaced repetition "
                    f"scheduling."
                )
            else:
                # Session complete, but more questions remain in topic
                numerator = session_score * questions_answered
                denominator = max(questions_answered, 1)
                score_percentage = int((numerator / denominator) * 100)
                completion_message = (
                    f"🎉 **Session Complete!**\n\n"
                    f"📊 **Your Results:**\n"
                    f"• Questions Answered: {questions_answered}\n"
                    f"• Session Score: {session_score:.1f}/{questions_answered} "
                    f"({score_percentage}%)\n\n"
                    f"Great progress! Your learning has been saved and will help "
                    f"optimize your future study sessions.\n\n"
                    f"Ready for another session? Choose a topic to continue your "
                    f"learning journey!"
                )

            response_data = {
                "isDone": True,
                "scores": {"overall": session_score},
                "message": completion_message,
                "final_score": session_score,
                "questions_answered": questions_answered,
                "total_questions": session_questions,
                "topic_progress": topic_progress,
                "total_topic_questions": total_topic_questions,
                "topic_complete": is_topic_complete,
            }
        else:
            # Continue with next question
            current_question_index = result.get("questionIndex", 1)
            next_question_text = result.get("nextQuestion", "Question not available")

            response_message = (
                f"⏭️ **Question Skipped**\n\n"
                f"**Question {current_question_index + 1}:**\n{next_question_text}"
            )

            response_data = {
                "isDone": False,
                "next_question": next_question_text,
                "message": response_message,
                "feedback": result.get("feedback", ""),
                "score": result["score"],
                "question_index": current_question_index,
                "total_questions": result.get("totalQuestions", 1),
            }

        return response_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error skipping question", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(
            status_code=500, detail=f"Failed to skip question: {safe_error_message}"
        )


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user),
):
    """End session early"""
    session_service = SessionService()

    # Verify session exists and user owns it
    session = await session_service.get_session(session_id, current_user.get("uid"))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        result = await session_service.end_session(session_id, current_user.get("uid"))
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error ending session", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(
            status_code=500, detail=f"Failed to end session: {safe_error_message}"
        )


# New Phase 3 Analytics Endpoints


@router.get("/{session_id}/analytics")
async def get_session_analytics(
    session_id: str, current_user: dict = Depends(get_current_user)
):
    """Get detailed analytics for a session"""
    session_service = SessionService()

    # Verify session exists and user owns it
    session = await session_service.get_session(session_id, current_user.get("uid"))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        analytics = await session_service.get_session_analytics(
            session_id, current_user.get("uid")
        )
        return analytics

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error getting analytics", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics: {safe_error_message}"
        )


@router.get("/user/{user_uid}/history")
async def get_user_session_history(
    user_uid: str, current_user: dict = Depends(get_current_user)
):
    """Get session history for a user"""
    # Verify user can access these sessions
    if current_user.get("uid") != user_uid:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        session_service = SessionService()
        history = await session_service.get_user_session_history(user_uid)
        return {"sessions": history}

    except Exception as e:
        logger.error("Error getting session history", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session history: {safe_error_message}",
        )
