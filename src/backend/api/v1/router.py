import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, UploadFile

from api.v1.endpoints import chat, questions, topics, voice

# Load environment variables
load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

api_router = APIRouter()


# Root endpoint for API validation (required by OpenAI client)
@api_router.get("/")
async def api_root():
    """
    Root API endpoint for validation and health checks.
    The OpenAI client makes GET requests to this endpoint to validate the API.
    """
    return {
        "name": "Spaced Repetition Backend API",
        "version": "v1",
        "status": "healthy",
        "endpoints": {
            "chat_completions": "/chat/completions",
            "topics": "/topics",
            "questions": "/topics/{topic_id}/questions",
            "voice": "/voice",
        },
    }


@api_router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Transcribe audio file using Deepgram API"""
    # Check if content type is supported (handle WebM with codecs)
    supported_types = ["audio/wav", "audio/x-wav", "audio/webm"]
    content_type = audio.content_type or ""

    # Check if content type starts with any of our supported types
    if not any(content_type.startswith(supported_type) for supported_type in supported_types):
        raise HTTPException(400, f"Unsupported audio format: {content_type}. Only WAV and WebM are supported.")

    if not DEEPGRAM_API_KEY:
        raise HTTPException(500, "Deepgram API key not configured")

    body = await audio.read()
    params = {"model": "nova-2-general", "language": "en", "punctuate": "true", "smart_format": "true"}
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": audio.content_type or "audio/wav"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post("https://api.deepgram.com/v1/listen", params=params, headers=headers, content=body)

    if resp.status_code != 200:
        raise HTTPException(502, f"Deepgram API error: {resp.status_code} - {resp.text}")

    data = resp.json()
    text = data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
    return {"transcript": text}


# Include endpoint routers
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(questions.router, tags=["questions"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
