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


class JoinRoomResponse(BaseModel):
    """Response model with room connection details."""

    room_name: str
    token: str
    server_url: str


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
        import uuid

        from livekit import api

        user_uid = current_user["uid"]

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
