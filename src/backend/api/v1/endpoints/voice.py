from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.plugins import (
    cartesia,
    deepgram,
    noise_cancellation,
    openai,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from pydantic import BaseModel

from app.config import Settings, get_settings
from core.monitoring.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class VoiceAgent(Agent):
    """Custom LiveKit Voice Agent for our spaced repetition system."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            instructions="""You are a helpful AI tutor for spaced repetition learning.
            You help users review and learn topics through conversational interaction.
            Be encouraging, clear, and educational in your responses."""
        )
        self.settings = settings


class CreateRoomRequest(BaseModel):
    """Request model for creating a new voice chat room."""

    user_id: str
    topic: Optional[str] = None


class JoinRoomResponse(BaseModel):
    """Response model with room connection details."""

    room_name: str
    token: str
    server_url: str


async def voice_agent_entrypoint(ctx: agents.JobContext, settings: Settings):
    """
    LiveKit agent entrypoint that handles voice interactions.
    This replaces the WebSocket-based voice endpoint.
    """
    logger.info(f"Starting voice agent for room: {ctx.room.name}")

    # Initialize the agent session with all required plugins
    session = AgentSession(
        # Use Deepgram for speech-to-text (you can switch to OpenAI Whisper if preferred)
        stt=deepgram.STT(
            model="nova-2-general",
            language="en",
            smart_format=True,
        ),
        # Use OpenAI for the LLM (same as your current implementation)
        llm=openai.LLM(
            model="gpt-4o-mini",  # or gpt-3.5-turbo
            api_key=settings.openai_api_key,
        ),
        # Use Cartesia for TTS (same as your current implementation)
        tts=cartesia.TTS(
            model_id="sonic-2",
            voice={"mode": "id", "id": "f9836c6e-a0bd-460e-9d3c-f7299fa60f94"},
            api_key=settings.cartesia_api_key,
        ),
        # Voice Activity Detection
        vad=silero.VAD.load(),
        # Turn detection for natural conversation flow
        turn_detection=MultilingualModel(),
    )

    # Start the session with the room and agent
    await session.start(
        room=ctx.room,
        agent=VoiceAgent(settings),
        room_input_options=RoomInputOptions(
            # Enhanced noise cancellation (remove if self-hosting)
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Connect to the room
    await ctx.connect()

    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user and offer to help them with their spaced repetition learning session."
    )

    logger.info("Voice agent session started successfully")


@router.post("/create-room", response_model=JoinRoomResponse)
async def create_voice_room(
    request: CreateRoomRequest,
    settings: Settings = Depends(get_settings),
):
    """
    Create a new LiveKit room for voice interaction.
    The voice agent will be automatically assigned via webhook or persistent worker.
    """
    try:
        import uuid

        from livekit import api

        # Generate unique room name
        room_name = f"voice-{request.user_id}-{uuid.uuid4().hex[:8]}"

        # Create room using LiveKit API
        if not hasattr(settings, "livekit_api_key") or not hasattr(settings, "livekit_api_secret"):
            raise HTTPException(
                status_code=500,
                detail="LiveKit credentials not configured. Please add LIVEKIT_API_KEY and LIVEKIT_API_SECRET to your environment.",
            )

        # Generate access token for the room
        token = (
            api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
            .with_identity(request.user_id)
            .with_name(f"User {request.user_id}")
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

        logger.info(f"Created voice room {room_name} for user {request.user_id}")

        # Note: The voice agent should be run as a persistent worker that listens for room events
        # Run: python voice_agent_worker.py
        # This will automatically connect to any room created

        return JoinRoomResponse(
            room_name=room_name,
            token=token,
            server_url=settings.livekit_server_url
            if hasattr(settings, "livekit_server_url")
            else "wss://your-livekit-server.com",
        )

    except Exception as e:
        logger.error(f"Failed to create voice room: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create voice room: {str(e)}")


@router.post("/start-agent")
async def start_voice_agent(
    settings: Settings = Depends(get_settings),
):
    """
    Start the LiveKit voice agent worker.
    This should typically be run as a separate service.
    """
    try:
        # Create worker options for the agent (for demonstration)
        # worker_options = agents.WorkerOptions(
        #     entrypoint_fnc=lambda ctx: voice_agent_entrypoint(ctx, settings),
        # )

        # This would typically run in a separate process/service
        # For development, you might want to run this manually
        logger.info("Voice agent worker configuration ready")

        return {
            "status": "Agent configuration ready",
            "message": "Run 'python -m livekit.agents.cli run' with this worker to start the agent service",
        }

    except Exception as e:
        logger.error(f"Failed to configure voice agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to configure voice agent: {str(e)}")


# Remove the old WebSocket and TTS endpoints since LiveKit handles this
# The /transcribe-and-chat and /ws/voice endpoints are no longer needed
# The /tts endpoint is replaced by real-time TTS through the LiveKit agent
