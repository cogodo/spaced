from fastapi import APIRouter

from api.v1.endpoints import chat, topics, voice

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
        "endpoints": {"chat_completions": "/chat/completions", "topics": "/topics", "voice": "/voice"},
    }


# Include endpoint routers
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
