#!/usr/bin/env python3
"""
Simplified LiveKit Voice Agent Worker

This agent handles:
1. Voice Activity Detection (VAD)
2. Speech-to-Text (STT)
3. Send transcripts to backend chat API
4. Text-to-Speech (TTS) from backend responses
5. Error handling via data channel messages

The agent does NOT handle conversation logic - that's all in the backend.

Usage:
    python voice_agent_worker.py dev

Environment Variables Required:
    - LIVEKIT_API_KEY: Your LiveKit API key
    - LIVEKIT_API_SECRET: Your LiveKit API secret
    - LIVEKIT_SERVER_URL: Your LiveKit server URL
    - OPENAI_API_KEY: OpenAI API key for STT (Whisper)
    - CARTESIA_API_KEY: Cartesia API key for TTS
    - DEEPGRAM_API_KEY: Deepgram API key for STT (optional, will use OpenAI if not provided)
    - BACKEND_URL: Backend API URL (auto-detected if not provided)
"""

import json
import logging
import os
import sys
from datetime import datetime

import aiohttp
import uvloop
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.plugins import cartesia, deepgram, openai, silero

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("voice_agent.log")],
)

logger = logging.getLogger(__name__)


def get_backend_url() -> str:
    """
    Determine the correct backend URL based on environment.

    Priority:
    1. BACKEND_URL environment variable (explicitly set)
    2. Environment detection based on other variables
    3. Default to localhost for development
    """
    # If BACKEND_URL is explicitly set, use it
    backend_url = os.getenv("BACKEND_URL")
    if backend_url:
        logger.info(f"Using explicit BACKEND_URL: {backend_url}")
        return backend_url

    # Detect environment based on other variables
    environment = os.getenv("ENVIRONMENT", "").lower()
    debug_mode = os.getenv("DEBUG", "True").lower() == "true"

    # Check for staging indicators
    is_staging = (
        environment == "staging"
        or "staging" in os.getenv("LIVEKIT_SERVER_URL", "").lower()
        or "staging" in os.getenv("FIREBASE_PROJECT_ID", "").lower()
    )

    # Check for production indicators
    is_production = (
        environment == "production"
        or not debug_mode
        or (
            "getspaced.app" in os.getenv("LIVEKIT_SERVER_URL", "")
            and "staging" not in os.getenv("LIVEKIT_SERVER_URL", "")
        )
    )

    # Determine backend URL
    if is_staging:
        backend_url = "https://api.staging.getspaced.app"
        logger.info("Detected staging environment, using staging backend URL")
    elif is_production:
        backend_url = "https://api.getspaced.app"
        logger.info("Detected production environment, using production backend URL")
    else:
        backend_url = "http://localhost:8000"
        logger.info("Detected development environment, using localhost backend URL")

    logger.info(f"Backend URL determined: {backend_url}")
    return backend_url


def validate_environment() -> dict[str, str]:
    """Validate and return required environment variables."""
    required_vars = {
        "LIVEKIT_API_KEY": "LiveKit API key",
        "LIVEKIT_API_SECRET": "LiveKit API secret",
        "LIVEKIT_SERVER_URL": "LiveKit server URL",
        "OPENAI_API_KEY": "OpenAI API key for STT",
        "CARTESIA_API_KEY": "Cartesia API key for TTS",
    }

    optional_vars = {
        "DEEPGRAM_API_KEY": "Deepgram API key for STT (will use OpenAI Whisper if not provided)",
        "BACKEND_URL": "Backend API URL (auto-detected if not provided)",
    }

    env_vars = {}
    missing_vars = []

    # Check required variables
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value:
            missing_vars.append(f"{var_name} ({description})")
        else:
            env_vars[var_name] = value
            logger.info(f"✓ {var_name}: {'*' * min(8, len(value))}... ({len(value)} chars)")

    # Check optional variables
    for var_name, description in optional_vars.items():
        value = os.getenv(var_name)
        if value:
            env_vars[var_name] = value
            logger.info(f"✓ {var_name}: {'*' * min(8, len(value))}... ({len(value)} chars)")
        else:
            logger.info(f"○ {var_name}: Not provided ({description})")

    if missing_vars:
        logger.error("❌ Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        sys.exit(1)

    logger.info("✅ All required environment variables are set")
    return env_vars


async def send_error_to_frontend(room: rtc.Room, error_message: str):
    """Send error message to frontend via data channel."""
    try:
        error_data = json.dumps(
            {"type": "voice_error", "message": error_message, "timestamp": datetime.now().isoformat()}
        )

        # Send to all participants
        await room.local_participant.publish_data(
            error_data.encode("utf-8"),
            destination_identities=[],  # Empty list means send to all
        )
        logger.info(f"Sent error to frontend: {error_message}")
    except Exception as e:
        logger.error(f"Failed to send error to frontend: {e}")


async def call_backend_chat_api(chat_id: str, transcript: str, user_id: str) -> str:
    """Call the backend chat API with the transcript."""
    backend_url = get_backend_url()

    # Use development token for authentication (in production, use service-to-service auth)
    dev_token = "dev-test-token"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{backend_url}/api/v1/chat/{chat_id}/messages",
                headers={"Authorization": f"Bearer {dev_token}", "Content-Type": "application/json"},
                json={"user_input": transcript},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["bot_response"]
                else:
                    error_text = await response.text()
                    logger.error(f"Backend API error {response.status}: {error_text}")
                    raise Exception(f"Backend API error: {response.status}")

    except Exception as e:
        logger.error(f"Failed to call backend chat API: {e}")
        raise


async def entrypoint(ctx: agents.JobContext):
    """
    Simplified voice agent entrypoint using proper LiveKit agents pattern.

    Flow: STT -> Backend Chat API -> TTS
    """
    logger.info(f"🎯 Simplified voice agent starting for room: {ctx.room.name}")

    # Validate environment
    env_vars = validate_environment()

    try:
        # Connect to room
        await ctx.connect()

        # Extract chat_id and user_id from room metadata
        chat_id = None
        user_id = None

        try:
            room_metadata = getattr(ctx.room, "metadata", {})
            if room_metadata:
                metadata = json.loads(room_metadata) if isinstance(room_metadata, str) else room_metadata
                chat_id = metadata.get("chat_id")
                user_id = metadata.get("user_id")
                logger.info(f"✅ Extracted chat_id: {chat_id}, user_id: {user_id}")
        except Exception as e:
            logger.error(f"Failed to parse room metadata: {e}")
            await send_error_to_frontend(ctx.room, "Failed to initialize voice session")
            return

        if not chat_id:
            logger.error("No chat_id found in room metadata")
            await send_error_to_frontend(ctx.room, "Invalid voice session configuration")
            return

        if not user_id:
            logger.error("No user_id found in room metadata")
            await send_error_to_frontend(ctx.room, "Authentication required for voice session")
            return

        # Set up STT (Speech-to-Text)
        if env_vars.get("DEEPGRAM_API_KEY"):
            logger.info("Using Deepgram for STT")
            stt = deepgram.STT(
                model="nova-2-general",
                language="en",
                smart_format=True,
                api_key=env_vars["DEEPGRAM_API_KEY"],
            )
        else:
            logger.info("Using OpenAI Whisper for STT")
            stt = openai.STT(api_key=env_vars["OPENAI_API_KEY"])

        # Set up TTS (Text-to-Speech)
        logger.info("Setting up Cartesia TTS")
        tts = cartesia.TTS(
            model="sonic-english",
            voice="95856005-0332-41b0-935f-352e296aa0df",
            language="en",
            api_key=env_vars["CARTESIA_API_KEY"],
        )

        # Set up VAD (Voice Activity Detection)
        vad = silero.VAD.load()

        # Use OpenAI LLM plugin but point it to our backend
        backend_url = get_backend_url()
        llm = openai.LLM(
            api_key="dev-test-token",  # Use our development token
            model="backend-voice",  # Can be any string, our backend ignores it
            base_url=f"{backend_url}/api/v1",  # Point to our backend
        )

        # Create a simple agent with chat_id in instructions for backend routing
        agent = agents.Agent(
            instructions=f"You are a helpful AI tutor for spaced repetition learning.\nchat_id:{chat_id}",
        )

        # Create agent session with our custom LLM
        session = agents.AgentSession(
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
        )

        # Start the session
        logger.info("🎧 Starting agent session...")
        await session.start(agent=agent, room=ctx.room)

        logger.info("✅ Voice agent session started successfully")

    except Exception as e:
        logger.error(f"❌ Error in voice agent: {e}", exc_info=True)
        await send_error_to_frontend(ctx.room, f"Voice agent error: {str(e)}")
        raise


def main():
    """Main entry point for the voice agent worker."""
    logger.info("🚀 Starting Simplified LiveKit Voice Agent Worker")

    # Validate environment first
    env_vars = validate_environment()

    # Set environment variables for LiveKit
    os.environ["LIVEKIT_URL"] = env_vars["LIVEKIT_SERVER_URL"]
    os.environ["LIVEKIT_API_KEY"] = env_vars["LIVEKIT_API_KEY"]
    os.environ["LIVEKIT_API_SECRET"] = env_vars["LIVEKIT_API_SECRET"]

    logger.info(f"🌐 Set LIVEKIT_URL to: {env_vars['LIVEKIT_SERVER_URL']}")
    logger.info(f"🔗 Backend URL: {get_backend_url()}")

    # Use uvloop for better performance
    if sys.platform != "win32":
        uvloop.install()

    # Create worker options
    worker_options = agents.WorkerOptions(entrypoint_fnc=entrypoint)

    try:
        logger.info("🎧 Starting LiveKit CLI-based worker...")
        agents.cli.run_app(worker_options)
    except KeyboardInterrupt:
        logger.info("👋 Voice agent worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Voice agent worker failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
