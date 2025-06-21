from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from pydantic import BaseModel
from core.models import Session
from core.services import SessionService
from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger

logger = get_logger("sessions_api")
router = APIRouter()


class StartSessionRequest(BaseModel):
    topicId: str


class ResponseRequest(BaseModel):
    answer: str


@router.post("/start")
async def start_session(
    request: StartSessionRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user)
):
    """Start a new learning session"""
    try:
        session_service = SessionService()
        session = await session_service.start_session(
            user_uid=current_user.get("uid"),
            topic_id=request.topicId
        )
        
        return {"sessionId": session.id}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error starting session", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {safe_error_message}")


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get session details and current question"""
    session_service = SessionService()
    
    session, question = await session_service.get_current_question(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify user owns this session
    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = {
        "session": session.dict(),
        "currentQuestion": question.dict() if question else None,
        "isComplete": question is None
    }
    
    return result


@router.post("/{session_id}/respond")
async def respond_to_question(
    session_id: str,
    request: ResponseRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user)
):
    """Submit response to current question"""
    session_service = SessionService()
    
    # Verify session exists and user owns it
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await session_service.submit_response(session_id, request.answer)
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error submitting response", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(status_code=500, detail=f"Failed to submit response: {safe_error_message}")


@router.post("/{session_id}/skip")
async def skip_question(
    session_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user)
):
    """Skip current question"""
    session_service = SessionService()
    
    # Verify session exists and user owns it
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await session_service.skip_question(session_id)
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error skipping question", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(status_code=500, detail=f"Failed to skip question: {safe_error_message}")


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user)
):
    """End session early"""
    session_service = SessionService()
    
    # Verify session exists and user owns it
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await session_service.end_session(session_id)
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error ending session", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(status_code=500, detail=f"Failed to end session: {safe_error_message}")


# New Phase 3 Analytics Endpoints

@router.get("/{session_id}/analytics")
async def get_session_analytics(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed analytics for a session"""
    session_service = SessionService()
    
    # Verify session exists and user owns it
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.userUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        analytics = await session_service.get_session_analytics(session_id)
        return analytics
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error getting analytics", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {safe_error_message}")


@router.get("/user/{user_uid}/history")
async def get_user_session_history(
    user_uid: str,
    current_user: dict = Depends(get_current_user)
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
        raise HTTPException(status_code=500, detail=f"Failed to get session history: {safe_error_message}") 