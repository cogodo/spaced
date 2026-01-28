"""
Voice Agent Worker - Simple LiveKit agent that connects voice to your backend.

Usage:
    pip install -e ".[voice]"
    python voice_agent_worker.py dev
"""

import json
import os

import aiohttp
from dotenv import load_dotenv
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import cartesia, deepgram, silero

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")

# Cartesia voice ID - "Reflective Woman" is good for tutoring
VOICE_ID = os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091")


class TutorAgent(Agent):
    """Voice tutor that routes speech to your backend."""

    def __init__(self, chat_id: str, user_id: str, auth_token: str):
        super().__init__(instructions="You are a helpful tutor for spaced repetition learning.")
        self.chat_id = chat_id
        self.user_id = user_id
        self.auth_token = auth_token

    async def on_user_turn_completed(self, turn_ctx, new_message):
        """Called when user finishes speaking."""
        transcript = new_message.content
        if not transcript:
            return

        print(f"[User]: {transcript}")

        # Call your backend
        response = await self._call_backend(transcript)
        print(f"[Agent]: {response}")

        # Speak the response
        await self.session.say(response)

    async def _call_backend(self, transcript: str) -> str:
        """Call your existing chat API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BACKEND_URL}/api/v1/chat/{self.chat_id}/messages",
                    json={"user_input": transcript},
                    headers={
                        "Authorization": f"Bearer {self.auth_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("bot_response", "I didn't catch that.")
                    else:
                        print(f"Backend error: {resp.status}")
                        return "Sorry, I'm having trouble connecting."
        except Exception as e:
            print(f"Backend call failed: {e}")
            return "Sorry, something went wrong."


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent."""
    print(f"Voice agent starting for room: {ctx.room.name}")

    await ctx.connect()

    # Get chat context from room metadata
    metadata = {}
    if ctx.room.metadata:
        try:
            metadata = json.loads(ctx.room.metadata)
        except json.JSONDecodeError:
            pass

    chat_id = metadata.get("chat_id", "voice-session")
    user_id = metadata.get("user_id", "")
    auth_token = metadata.get("auth_token", "")

    # Create agent session with STT/TTS
    session = AgentSession(
        stt=deepgram.STT(model="nova-2", api_key=DEEPGRAM_API_KEY),
        tts=cartesia.TTS(voice=VOICE_ID, api_key=CARTESIA_API_KEY),
        vad=silero.VAD.load(),
    )

    # Create and start the agent
    agent = TutorAgent(chat_id=chat_id, user_id=user_id, auth_token=auth_token)
    await session.start(agent=agent, room=ctx.room)

    # Greet the user
    await session.say("Hi! I'm ready to help you learn. What would you like to study?")

    print("Voice agent session started")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
