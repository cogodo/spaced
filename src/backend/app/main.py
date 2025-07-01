import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.v1.router import api_router
from app.config import settings
from infrastructure.firebase import initialize_firebase
from infrastructure.redis import close_redis, initialize_redis


def create_app() -> FastAPI:
    app = FastAPI(
        title="Learning Chatbot API",
        description="Spaced repetition learning chatbot with Firebase integration",
        version="1.0.0",
    )

    # CORS middleware
    # Use a more permissive policy for local development
    if settings.is_development:
        # Allow common local origins for development
        allow_origins = [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ]
    else:
        # Use a strict policy for production
        allow_origins = settings.cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup"""
        print(f"Server starting in '{settings.environment}' mode.")
        print(f"Allowed CORS origins: {allow_origins}")
        try:
            initialize_firebase()
            print("Firebase initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            # Don't fail startup - let endpoints handle the error

        try:
            await initialize_redis()
            print("Redis initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Redis: {e}")
            # Continue without Redis - will fallback to Firebase only

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown"""
        try:
            await close_redis()
            print("Redis connection closed")
        except Exception as e:
            print(f"Error closing Redis: {e}")

    # Include API routes
    app.include_router(api_router, prefix=settings.api_prefix)
    app.include_router(health_router, tags=["health"])

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
