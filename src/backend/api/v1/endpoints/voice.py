import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.v1.dependencies import get_current_user
from app.config import Settings, get_settings
from core.monitoring.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class CreateRoomRequest(BaseModel):
    """Request model for creating a new voice chat room."""

    chat_id: str  # Link to existing chat session
    auth_token: str = ""  # Auth token for voice agent to call backend APIs


class JoinRoomResponse(BaseModel):
    """Response model with room connection details."""

    room_name: str
    token: str
    server_url: str


class EndVoiceSessionRequest(BaseModel):
    """Request to end a voice session."""

    room_name: str


@router.get("/health")
async def voice_health_check():
    """
    Health check for voice services.

    In Railway/microservices deployment, the voice agent runs as a separate service.
    This endpoint just checks if LiveKit is configured on the main backend.
    """
    try:
        health_status = {
            "status": "healthy",
            "voice_agent": "separate_service",  # Voice agent runs in its own container
            "configuration": {},
            "warnings": [],
        }

        # Check LiveKit configuration (required for creating rooms)
        livekit_vars = {
            "LIVEKIT_API_KEY": "LiveKit API key",
            "LIVEKIT_API_SECRET": "LiveKit API secret",
            "LIVEKIT_SERVER_URL": "LiveKit server URL",
        }

        all_livekit_configured = True
        for var_name, description in livekit_vars.items():
            value = os.getenv(var_name)
            if value:
                health_status["configuration"][var_name] = "set"
            else:
                health_status["configuration"][var_name] = "missing"
                health_status["warnings"].append(f"Missing: {var_name}")
                all_livekit_configured = False

        if all_livekit_configured:
            health_status["livekit"] = "configured"
        else:
            health_status["livekit"] = "not_configured"
            health_status["status"] = "degraded"

        logger.info("Voice health check passed")
        return health_status

    except Exception as e:
        logger.error(f"Voice health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Voice service error: {str(e)}")


@router.post("/create-room", response_model=JoinRoomResponse)
async def create_voice_room(
    request: CreateRoomRequest,
    settings: Settings = Depends(get_settings),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new LiveKit room for voice interaction linked to a chat session.
    The voice agent will handle STT -> backend chat API -> TTS flow.
    """
    try:
        import json
        import uuid

        from livekit import api

        user_uid = current_user["uid"]

        # Room metadata passed to voice agent
        room_metadata = {
            "chat_id": request.chat_id,
            "user_id": user_uid,
            "auth_token": request.auth_token,
        }

        # Generate unique room name with chat ID for easier debugging
        room_name = f"voice-chat-{request.chat_id}-{uuid.uuid4().hex[:8]}"

        # Check for LiveKit credentials
        if not settings.livekit_api_key or not settings.livekit_api_secret:
            raise HTTPException(
                status_code=500,
                detail="LiveKit credentials not configured. Please set LIVEKIT_API_KEY and LIVEKIT_API_SECRET.",
            )

        # Use LiveKit server URL if available, otherwise default
        livekit_server_url = settings.livekit_server_url or "wss://your-livekit-server.com"

        # Create room using LiveKit API
        lkapi = api.LiveKitAPI(
            url=livekit_server_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )

        # Create room with chat_id in metadata
        room_info = await lkapi.room.create_room(
            api.CreateRoomRequest(name=room_name, metadata=json.dumps(room_metadata))
        )

        # Close the API client
        await lkapi.aclose()

        logger.info(f"Created voice room {room_name} for chat {request.chat_id}")

        # Generate access token for the room
        token = (
            api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
            .with_identity(user_uid)
            .with_name(f"User {user_uid}")
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .to_jwt()
        )

        return JoinRoomResponse(
            room_name=room_name,
            token=token,
            server_url=settings.livekit_server_url
            if hasattr(settings, "livekit_server_url")
            else "wss://your-livekit-server.com",
        )

    except Exception as e:
        logger.error(f"Failed to create voice room for chat {request.chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create voice room: {str(e)}")


@router.post("/end-session")
async def end_voice_session(
    request: EndVoiceSessionRequest,
    settings: Settings = Depends(get_settings),
    current_user: dict = Depends(get_current_user),
):
    """
    End a voice session by deleting the LiveKit room.
    This will automatically disconnect all participants including the voice agent.
    """
    try:
        from livekit import api

        if not settings.livekit_api_key or not settings.livekit_api_secret:
            raise HTTPException(
                status_code=500,
                detail="LiveKit credentials not configured.",
            )

        livekit_server_url = settings.livekit_server_url or "wss://your-livekit-server.com"

        lkapi = api.LiveKitAPI(
            url=livekit_server_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )

        # Delete the room - this disconnects all participants
        await lkapi.room.delete_room(api.DeleteRoomRequest(room=request.room_name))
        await lkapi.aclose()

        logger.info(f"Deleted voice room {request.room_name}")
        return {"status": "success", "message": f"Voice session ended for room {request.room_name}"}

    except Exception as e:
        logger.error(f"Failed to end voice session for room {request.room_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to end voice session: {str(e)}")
