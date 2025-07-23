#!/usr/bin/env python3
"""
LiveKit Voice Agent Worker

This script runs the voice agent that handles real-time voice interactions
using LiveKit's agent framework with STT, LLM, and TTS capabilities.

Usage:
    # Run as a persistent worker (listens for all rooms)
    python voice_agent_worker.py

    # Run for a specific room (spawned by backend)
    python voice_agent_worker.py --room-name <room-name> --worker-type room

Environment Variables Required:
    - LIVEKIT_API_KEY: Your LiveKit API key
    - LIVEKIT_API_SECRET: Your LiveKit API secret
    - LIVEKIT_SERVER_URL: Your LiveKit server URL
    - OPENAI_API_KEY: OpenAI API key for LLM
    - CARTESIA_API_KEY: Cartesia API key for TTS
    - DEEPGRAM_API_KEY: Deepgram API key for STT (optional)
"""

import argparse
import logging
import os
import sys

import uvloop
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import JobRequest
from livekit.plugins import (
    cartesia,
    deepgram,
    openai,
    silero,
)

# Load environment variables from .env file
load_dotenv()

# from livekit.plugins.turn_detector.multilingual import MultilingualModel  # Disabled

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("voice_agent.log")],
)

logger = logging.getLogger(__name__)


def validate_environment() -> dict[str, str]:
    """Validate and return required environment variables."""
    required_vars = {
        "LIVEKIT_API_KEY": "LiveKit API key",
        "LIVEKIT_API_SECRET": "LiveKit API secret",
        "LIVEKIT_SERVER_URL": "LiveKit server URL",
        "OPENAI_API_KEY": "OpenAI API key",
        "CARTESIA_API_KEY": "Cartesia API key for TTS",
    }

    optional_vars = {
        "DEEPGRAM_API_KEY": "Deepgram API key for STT (will use OpenAI Whisper if not provided)",
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
        logger.error("\nPlease set these environment variables and try again.")
        logger.error("See env.example for details on how to obtain these keys.")
        sys.exit(1)

    logger.info("✅ All required environment variables are set")
    return env_vars


# Define function tools for the agent
@agents.function_tool
async def get_user_topics(
    context: agents.RunContext,
    subject_area: str = "any",
) -> str:
    """Get available topics for spaced repetition review.

    Args:
        subject_area: The subject area to get topics for (e.g., "math", "science", "history")
    """
    logger.info(f"Getting topics for subject area: {subject_area}")

    # In a real implementation, this would call your backend API
    # For now, return some example topics
    example_topics = {
        "math": ["Algebra", "Calculus", "Geometry", "Statistics"],
        "science": ["Physics", "Chemistry", "Biology", "Earth Science"],
        "history": ["World War I", "Ancient Rome", "Renaissance", "Cold War"],
        "any": ["General Knowledge", "Random Facts", "Mixed Topics"],
    }

    topics = example_topics.get(subject_area.lower(), example_topics["any"])
    return f"Available topics for {subject_area}: {', '.join(topics)}"


@agents.function_tool
async def start_review_session(context: agents.RunContext, topic: str, difficulty: str = "medium") -> str:
    """Start a spaced repetition review session for a specific topic.

    Args:
        topic: The topic to review (e.g., "Algebra", "World War I")
        difficulty: The difficulty level ("easy", "medium", "hard")
    """
    logger.info(f"Starting review session - Topic: {topic}, Difficulty: {difficulty}")

    # In a real implementation, this would:
    # 1. Call your backend API to get questions
    # 2. Initialize the review session
    # 3. Get the first question

    return f"Starting {difficulty} level review session for {topic}. I'll present you with questions and you can answer them. Ready for your first question?"


async def entrypoint(ctx: agents.JobContext):
    """
    Main entrypoint for the LiveKit voice agent following best practices.

    This function is called whenever a new session starts.
    """
    logger.info(f"🎯 Voice agent starting for room: {ctx.room.name}")
    logger.info(f"Room SID: {ctx.room.sid}")

    # Validate environment on each session start
    env_vars = validate_environment()

    try:
        # Connect to the room first (best practice)
        logger.info("Connecting to room...")
        await ctx.connect()

        # Set up STT (Speech-to-Text)
        if env_vars.get("DEEPGRAM_API_KEY"):
            logger.info("Using Deepgram for STT")
            stt = deepgram.STT(
                model="nova-3",  # Updated to nova-3 as shown in best practices
                language="en",
                smart_format=True,
                api_key=env_vars["DEEPGRAM_API_KEY"],
            )
        else:
            logger.info("Using OpenAI Whisper for STT")
            stt = openai.STT(
                api_key=env_vars["OPENAI_API_KEY"],
            )

        # Set up LLM (Large Language Model)
        logger.info("Setting up OpenAI LLM")
        llm = openai.LLM(
            model="gpt-4o-mini",
            api_key=env_vars["OPENAI_API_KEY"],
        )

        # Set up TTS (Text-to-Speech)
        logger.info("Setting up Cartesia TTS")
        tts = cartesia.TTS(
            model="sonic-2",
            voice="f9836c6e-a0bd-460e-9d3c-f7299fa60f94",  # Voice ID as string
            language="en",
            api_key=env_vars["CARTESIA_API_KEY"],
        )

        # Set up VAD (Voice Activity Detection)
        logger.info("Setting up Silero VAD")
        vad = silero.VAD.load()

        # Create Agent with instructions and tools (best practice pattern)
        logger.info("Creating spaced repetition agent...")
        agent = agents.Agent(
            instructions="""
            You are a friendly and encouraging spaced repetition learning assistant built by LiveKit.

            Your role is to:
            1. Help users review topics using spaced repetition techniques
            2. Present questions and evaluate their answers
            3. Provide helpful feedback and explanations
            4. Track their progress and adjust difficulty accordingly
            5. Keep the session engaging and motivating

            Always be supportive and educational. If a user gets something wrong,
            explain the correct answer and why it's important to understand.
            """,
            tools=[get_user_topics, start_review_session],
        )

        # Create agent session with all components
        logger.info("Creating agent session...")
        session = agents.AgentSession(
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
            # turn_detection disabled to avoid model download requirement
        )

        # Start the session with agent and room (best practice)
        logger.info("Starting agent session...")
        await session.start(agent=agent, room=ctx.room)

        # Generate initial greeting
        logger.info("Generating initial greeting...")
        await session.generate_reply(
            instructions="Greet the user warmly and offer to help them with their spaced repetition learning session. Ask what topic they'd like to review or learn about today."
        )

        logger.info("🎉 Voice agent session started successfully!")

    except Exception as e:
        logger.error(f"❌ Error in voice agent session: {e}", exc_info=True)
        raise


def main():
    """Main entry point for the voice agent worker."""
    # Check if this is a CLI command (dev, start, etc.)
    if len(sys.argv) > 1 and sys.argv[1] in ["dev", "start", "connect", "console"]:
        # This is a CLI command, handle it with LiveKit CLI
        logger.info("🚀 Starting LiveKit Voice Agent Worker via CLI")

        # Validate and set environment variables first
        env_vars = validate_environment()
        os.environ["LIVEKIT_URL"] = env_vars["LIVEKIT_SERVER_URL"]
        os.environ["LIVEKIT_API_KEY"] = env_vars["LIVEKIT_API_KEY"]
        os.environ["LIVEKIT_API_SECRET"] = env_vars["LIVEKIT_API_SECRET"]

        logger.info(f"🌐 Set LIVEKIT_URL to: {env_vars['LIVEKIT_SERVER_URL']}")

        # Set the event loop policy for better performance
        if sys.platform != "win32":
            uvloop.install()

        # Create worker options for CLI
        worker_options = agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
        )

        # Use the CLI system
        try:
            logger.info("🎧 Starting LiveKit CLI-based worker...")
            agents.cli.run_app(worker_options)
        except KeyboardInterrupt:
            logger.info("👋 Voice agent worker stopped by user")
        except Exception as e:
            logger.error(f"❌ Voice agent worker failed: {e}", exc_info=True)
            sys.exit(1)
    else:
        # This is our custom mode (room-specific or default worker)
        parser = argparse.ArgumentParser(description="LiveKit Voice Agent Worker")
        parser.add_argument("--room-name", type=str, help="Specific room to join")
        parser.add_argument(
            "--worker-type",
            type=str,
            choices=["room", "worker"],
            default="worker",
            help="Agent type: room-specific or persistent worker",
        )
        args = parser.parse_args()

        logger.info("🚀 Starting LiveKit Voice Agent Worker (Custom Mode)")
        logger.info(f"Mode: {args.worker_type}")
        if args.room_name:
            logger.info(f"Room: {args.room_name}")

        # Validate environment first
        env_vars = validate_environment()

        # Set environment variables that LiveKit CLI expects
        os.environ["LIVEKIT_URL"] = env_vars["LIVEKIT_SERVER_URL"]
        os.environ["LIVEKIT_API_KEY"] = env_vars["LIVEKIT_API_KEY"]
        os.environ["LIVEKIT_API_SECRET"] = env_vars["LIVEKIT_API_SECRET"]

        logger.info(f"🌐 Set LIVEKIT_URL to: {env_vars['LIVEKIT_SERVER_URL']}")

        # Set the event loop policy for better performance
        if sys.platform != "win32":
            uvloop.install()

        # Create worker options
        worker_options = agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
        )

        # If running for a specific room, configure the request handler
        if args.worker_type == "room" and args.room_name:
            # For room-specific mode, only accept jobs for the specified room
            async def request_handler(req: JobRequest) -> bool:
                # Accept the job only if it's for our specific room
                should_accept = req.room.name == args.room_name
                if should_accept:
                    logger.info(f"Accepting job for room: {req.room.name}")
                else:
                    logger.info(f"Rejecting job for room: {req.room.name} (waiting for {args.room_name})")
                return should_accept

            worker_options.request_handler = request_handler
            worker_options.disconnect_on_room_close = True

        # Use the CLI system which properly handles environment variables
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
