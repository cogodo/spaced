import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.router import api_router
from app.config import settings
from core.monitoring.logger import get_logger
from infrastructure.firebase import initialize_firebase
from infrastructure.redis import close_redis, initialize_redis

# Initialize logger
logger = get_logger("main")


def create_app() -> FastAPI:
    """
    Application factory, creating and configuring the FastAPI application.
    """
    app = FastAPI(
        title="Learning Chatbot API",
        description="Spaced repetition learning chatbot with Firebase integration",
        version="1.0.0",
    )

    # Configure CORS
    if settings.is_development:
        allow_origins = [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8080",
        ]
    else:
        # In production, use a comma-separated string from settings
        allow_origins = settings.cors_origins.split(",") if settings.cors_origins else []

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Event Handlers ---
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on application startup."""
        print(f"Server starting in '{settings.environment}' mode.")

        # --- Configuration Checks ---
        if not settings.openai_api_key:
            logger.critical("FATAL: OPENAI_API_KEY is not set. The application cannot start.")
            raise ValueError("OPENAI_API_KEY is not set. Please configure your environment.")

        # --- Initializations ---
        try:
            initialize_firebase()
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"ERROR: Failed to initialize Firebase: {e}")

        try:
            await initialize_redis()
            print("Redis initialized successfully.")
        except Exception as e:
            print(f"WARNING: Failed to initialize Redis: {e}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on application shutdown."""
        try:
            await close_redis()
            print("Redis connection closed.")
        except Exception as e:
            print(f"ERROR: Failed to close Redis connection: {e}")

    # --- Routers ---
    # The main API router for version 1
    app.include_router(api_router, prefix="/api/v1")

    # Note: The /monitoring router is now the primary source for health checks.
    # The old health_router has been removed.

    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
