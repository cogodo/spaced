from fastapi import APIRouter
from api.v1.endpoints import sessions, topics, chat

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"]) 