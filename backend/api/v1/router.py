from fastapi import APIRouter
from api.v1.endpoints import sessions, topics

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(topics.router, prefix="/topics", tags=["topics"]) 