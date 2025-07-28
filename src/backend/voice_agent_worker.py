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
    - GOOGLE_APPLICATION_CREDENTIALS: Path to Firebase service account JSON file
"""

import json
import logging
import os
import sys
from datetime import datetime

import aiohttp
import firebase_admin
import uvloop
from dotenv import load_dotenv
from firebase_admin import auth, credentials
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

# Firebase app instance for token generation
_firebase_app = None


def initialize_firebase_for_voice_agent():
    """Initialize Firebase Admin SDK for the voice agent to generate custom tokens."""
    global _firebase_app

    if _firebase_app:
        return _firebase_app

    try:
        # Check if Firebase is already initialized
        if firebase_admin._DEFAULT_APP_NAME in firebase_admin._apps:
            _firebase_app = firebase_admin.get_app()
            logger.info("Using existing Firebase app")
            return _firebase_app

        # Initialize Firebase with service account credentials
        credential_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credential_path or not os.path.exists(credential_path):
            raise Exception(f"Firebase service account credentials not found at: {credential_path}")

        logger.info(f"Initializing Firebase with credentials from: {credential_path}")
        cred = credentials.Certificate(credential_path)
        _firebase_app = firebase_admin.initialize_app(cred, name="voice_agent")
        logger.info("Firebase initialized successfully for voice agent")
        return _firebase_app

    except Exception as e:
        logger.error(f"Failed to initialize Firebase for voice agent: {e}")
        raise


def generate_service_token():
    """Generate a Firebase custom token and exchange it for an ID token for service-to-service authentication."""
    try:
        if not _firebase_app:
            initialize_firebase_for_voice_agent()

        # Create a custom token for the voice agent service
        # Use a special UID that identifies this as a service account
        service_uid = "voice-agent-service"
        custom_token = auth.create_custom_token(
            service_uid,
            {"service": "voice_agent", "permissions": ["chat_api_access"], "issued_at": datetime.utcnow().isoformat()},
            app=_firebase_app,  # Explicitly use our voice agent app
        )

        logger.info("Generated custom token for voice agent")

        # Exchange custom token for ID token
        # We need to use Firebase Auth REST API to exchange the token
        import requests

        # Get the project ID from the service account
        project_id = os.getenv("FIREBASE_PROJECT_ID", "spaced-b571d")

        # Exchange custom token for ID token
        exchange_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
        params = {
            "key": os.getenv("FIREBASE_WEB_API_KEY"),  # We need the web API key
            "token": custom_token.decode(),
            "returnSecureToken": True,
        }

        response = requests.post(exchange_url, params=params)
        if response.status_code == 200:
            id_token = response.json()["idToken"]
            logger.info("Successfully exchanged custom token for ID token")
            return id_token
        else:
            logger.error(f"Failed to exchange custom token: {response.status_code} - {response.text}")
            raise Exception(f"Token exchange failed: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to generate service token: {e}")
        raise


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
    """Validate that all required environment variables are set."""
    required_vars = {
        "LIVEKIT_API_KEY": os.getenv("LIVEKIT_API_KEY"),
        "LIVEKIT_API_SECRET": os.getenv("LIVEKIT_API_SECRET"),
        "LIVEKIT_SERVER_URL": os.getenv("LIVEKIT_SERVER_URL"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "CARTESIA_API_KEY": os.getenv("CARTESIA_API_KEY"),
        "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        "FIREBASE_WEB_API_KEY": os.getenv("FIREBASE_WEB_API_KEY"),
    }

    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Log successful validation (without exposing secrets)
    logger.info("✓ LIVEKIT_API_KEY: " + "*" * 15 + "...")
    logger.info("✓ LIVEKIT_API_SECRET: " + "*" * 43 + "...")
    logger.info("✓ LIVEKIT_SERVER_URL: " + "*" * 35 + "...")
    logger.info("✓ OPENAI_API_KEY: " + "*" * 164 + "...")
    logger.info("✓ CARTESIA_API_KEY: " + "*" * 29 + "...")
    logger.info("✓ GOOGLE_APPLICATION_CREDENTIALS: " + "*" * 33 + "...")
    logger.info("✓ FIREBASE_WEB_API_KEY: " + "*" * 39 + "...")

    # Optional Deepgram API key
    if os.getenv("DEEPGRAM_API_KEY"):
        logger.info("✓ DEEPGRAM_API_KEY: " + "*" * 40 + "...")
        required_vars["DEEPGRAM_API_KEY"] = os.getenv("DEEPGRAM_API_KEY")

    return required_vars


async def send_error_to_frontend(room: rtc.Room, error_message: str):
    """Send error message to frontend via data channel."""
    try:
        data = {
            "type": "voice_error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await room.local_participant.publish_data(
            json.dumps(data).encode(),
            reliable=True,
        )
        logger.error(f"Sent error to frontend: {error_message}")
    except Exception as e:
        logger.error(f"Failed to send error to frontend: {e}")


async def call_backend_chat_api(chat_id: str, transcript: str, user_id: str) -> str:
    """Call the backend chat API with the transcript."""
    backend_url = get_backend_url()

    # Generate a service token for authentication
    service_token = generate_service_token()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{backend_url}/api/v1/chat/{chat_id}/messages",
                headers={"Authorization": f"Bearer {service_token}", "Content-Type": "application/json"},
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
        service_token = generate_service_token()
        llm = openai.LLM(
            api_key=service_token,  # Use our service token
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
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        # Development mode - run directly
        logger.info("🚀 Starting Simplified LiveKit Voice Agent Worker")

        # Validate environment
        env_vars = validate_environment()
        logger.info(f"✓ BACKEND_URL: {get_backend_url()}")

        # Initialize Firebase for token generation
        initialize_firebase_for_voice_agent()

        # Test token generation
        try:
            token = generate_service_token()
            logger.info("✓ Service token generation test successful")
        except Exception as e:
            logger.error(f"✗ Service token generation test failed: {e}")
            sys.exit(1)

        logger.info("✅ Voice agent worker ready for development")
    else:
        # Production mode - run with LiveKit agents CLI
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
