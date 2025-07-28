import os
import subprocess

import psutil
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


@router.get("/health")
async def voice_health_check():
    """Health check for voice services."""
    try:
        health_status = {"status": "healthy", "voice_agent": "unknown", "configuration": {}, "errors": []}

        # Check if voice agent worker process is running
        voice_agent_running = False
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["cmdline"] and any("voice_agent_worker.py" in cmd for cmd in proc.info["cmdline"]):
                    voice_agent_running = True
                    health_status["voice_agent"] = "running"
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not voice_agent_running:
            health_status["voice_agent"] = "not_running"
            health_status["errors"].append("Voice agent worker process not found")

        # Check required environment variables
        required_vars = {
            "LIVEKIT_API_KEY": "LiveKit API key",
            "LIVEKIT_API_SECRET": "LiveKit API secret",
            "LIVEKIT_SERVER_URL": "LiveKit server URL",
            "CARTESIA_API_KEY": "Cartesia TTS API key",
        }

        optional_vars = {
            "DEEPGRAM_API_KEY": "Deepgram STT API key (optional)",
            "BACKEND_URL": "Backend API URL (auto-detected if not provided)",
            "ENVIRONMENT": "Environment (development/staging/production)",
        }

        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            if value:
                health_status["configuration"][var_name] = "set"
            else:
                health_status["configuration"][var_name] = "missing"
                health_status["errors"].append(f"Missing required environment variable: {var_name}")

        for var_name, description in optional_vars.items():
            value = os.getenv(var_name)
            if value:
                health_status["configuration"][var_name] = "set"
            else:
                health_status["configuration"][var_name] = "not_set"

        # Check if systemd service is active (if running as systemd)
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "voice-agent.service"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                health_status["systemd_service"] = "active"
            else:
                health_status["systemd_service"] = "inactive"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            health_status["systemd_service"] = "unknown"

        # Determine overall health status
        if health_status["errors"]:
            health_status["status"] = "unhealthy"
            raise HTTPException(status_code=503, detail=health_status)

        logger.info("Voice health check passed")
        return health_status

    except Exception as e:
        logger.error(f"Voice health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Voice service unhealthy: {str(e)}")


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

        # Lightweight metadata - chat_id only (authentication will be handled differently)
        room_metadata = {
            "chat_id": request.chat_id,
            "user_id": user_uid,
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
