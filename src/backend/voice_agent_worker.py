"""
Voice Agent Worker - LiveKit agent that connects voice to your backend.

Uses the llm_node to route speech through your custom backend API.

Usage:
    pip install -e ".[voice]"
    python voice_agent_worker.py dev
"""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, AsyncIterable

import aiohttp
from dotenv import load_dotenv
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, llm
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()


# --- Simple Health Check Server for Railway ---
class HealthHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for health checks."""

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "voice-agent"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging to avoid noise
        pass


def start_health_server():
    """Start a background health check server for Railway."""
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()


# Start health server in background thread
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Cartesia voice ID - Browse voices at https://play.cartesia.ai/
# Good options for tutoring:
#   "a0e99841-438c-4a64-b679-ae501e7d6091" - Reflective Woman (calm, clear)
#   "c2ac25f9-ecc4-4f56-9095-651354df60c0" - Sarah (natural conversational)
#   "bf991597-6c13-47e4-8411-91ec2de5c466" - Confident Woman
#   "79a125e8-cd45-4c13-8a67-188112f4dd22" - British Lady
VOICE_ID = os.getenv("CARTESIA_VOICE_ID", "f9836c6e-a0bd-460e-9d3c-f7299fa60f94")

# TTS speed multiplier (1.0 = normal, 1.25 = slightly faster, 1.5 = 50% faster)
# Note: Higher speeds can cause audio artifacts - 1.2-1.3 is usually the sweet spot
TTS_SPEED = float(os.getenv("TTS_SPEED", "1"))


SESSION_COMPLETION_MARKERS = [
    "Session completed!",
    "session has already been completed",
    "Session ended!",
    "Here's your summary:",
    "completed all the questions",
    "run out of questions",
]


class TutorAgent(Agent):
    """Voice tutor that routes speech to your backend using llm_node."""

    def __init__(self, chat_id: str, user_id: str, auth_token: str):
        super().__init__(
            instructions="You are a helpful tutor for spaced repetition learning.",
        )
        self.chat_id = chat_id
        self.user_id = user_id
        self.auth_token = auth_token
        self.session_completed = False

    async def llm_node(
        self, chat_ctx: llm.ChatContext, tools: list, model_settings: Any = None
    ) -> AsyncIterable[llm.ChatChunk]:
        """
        Override the LLM node to call our custom backend instead of OpenAI.
        This is called when the user finishes speaking and the agent needs to respond.
        """
        # Collect consecutive user messages (in case user spoke multiple times)
        user_messages = []
        for msg in reversed(chat_ctx.items):
            if msg.role == "user":
                msg_text = ""
                if isinstance(msg.content, str):
                    msg_text = msg.content
                elif isinstance(msg.content, list):
                    # Handle list content format
                    for item in msg.content:
                        if isinstance(item, str):
                            msg_text += item
                        elif hasattr(item, "text"):
                            msg_text += item.text
                if msg_text:
                    user_messages.append(msg_text)
            elif msg.role == "assistant" and user_messages:
                # Stop when we hit an assistant message (after collecting user messages)
                break

        # Reverse to get chronological order and join
        user_messages.reverse()
        user_message = " ".join(user_messages)

        print(f"[User said]: {user_message}")

        # If session already completed, don't process further
        if self.session_completed:
            print("[Session already completed - ignoring input]")
            yield llm.ChatChunk(
                id="completed",
                delta=llm.ChoiceDelta(
                    role="assistant",
                    content="This session has ended. Please start a new session to continue learning.",
                ),
            )
            return

        if not user_message:
            yield llm.ChatChunk(
                id="empty",
                delta=llm.ChoiceDelta(role="assistant", content="I didn't catch that. Could you repeat?"),
            )
            return

        # Call our backend and track full response for completion detection
        full_response = ""
        try:
            async for chunk in self._call_backend_streaming(user_message):
                # Extract content from chunk for completion detection
                if chunk.delta and chunk.delta.content:
                    full_response += chunk.delta.content
                yield chunk
        except Exception as e:
            print(f"[Error calling backend]: {e}")
            yield llm.ChatChunk(
                id="error",
                delta=llm.ChoiceDelta(role="assistant", content="Sorry, I'm having trouble right now."),
            )
            return

        # Check if response indicates session completion
        if any(marker in full_response for marker in SESSION_COMPLETION_MARKERS):
            print("[Session completed - client should call /voice/end-session to disconnect]")
            self.session_completed = True

    async def _call_backend_streaming(self, transcript: str) -> AsyncIterable[llm.ChatChunk]:
        """Call our backend API and yield ChatChunks."""
        print(f"[Calling backend]: {BACKEND_URL}/api/v1/chat/completions")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/v1/chat/completions",
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": f"chat_id:{self.chat_id}\nuser_id:{self.user_id}",
                        },
                        {
                            "role": "user",
                            "content": transcript,
                        },
                    ],
                    "stream": True,
                },
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"[Backend error]: {resp.status} - {error_text}")
                    yield llm.ChatChunk(
                        id="error",
                        delta=llm.ChoiceDelta(
                            role="assistant", content="Sorry, I'm having trouble connecting to the backend."
                        ),
                    )
                    return

                # Parse SSE stream and yield ChatChunks
                buffer = ""
                chunk_id = 0
                async for chunk in resp.content.iter_any():
                    buffer += chunk.decode("utf-8")

                    # Process complete SSE messages
                    while "\n\n" in buffer:
                        message, buffer = buffer.split("\n\n", 1)

                        for line in message.split("\n"):
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    continue

                                try:
                                    data = json.loads(data_str)
                                    choices = data.get("choices", [])
                                    if choices:
                                        delta = choices[0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            print(f"[Chunk]: {content}")
                                            yield llm.ChatChunk(
                                                id=f"chunk-{chunk_id}",
                                                delta=llm.ChoiceDelta(role="assistant", content=content),
                                            )
                                            chunk_id += 1
                                except json.JSONDecodeError:
                                    pass


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

    print(f"Voice agent config: chat_id={chat_id}, user_id={user_id[:8] if user_id else 'none'}...")

    # Create the agent
    agent = TutorAgent(
        chat_id=chat_id,
        user_id=user_id,
        auth_token=auth_token,
    )

    # Create agent session with STT, TTS, VAD, and LLM pointed at our backend
    # The llm_node override in our Agent class will intercept and call our backend
    # We use OpenAI LLM pointed at our backend URL as the "LLM" - our llm_node does the actual work
    session = AgentSession(
        stt=deepgram.STT(model="nova-2", api_key=DEEPGRAM_API_KEY),
        # Use sonic-2-2025-03-07 model which supports speed control
        tts=cartesia.TTS(
            voice=VOICE_ID,
            api_key=CARTESIA_API_KEY,
            model="sonic-3",
            speed=TTS_SPEED,
        ),
        vad=silero.VAD.load(),
        llm=openai.LLM(
            model="gpt-4",  # Doesn't matter - our llm_node overrides this
            base_url=f"{BACKEND_URL}/api/v1",
            api_key=auth_token or "dummy",  # Use auth token as API key
        ),
    )
    print(f"TTS speed set to {TTS_SPEED}x")

    # Start the session
    await session.start(agent=agent, room=ctx.room)

    # No greeting - agent ties into the current topic context from the chat session
    print("Voice agent session started - listening for speech...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
