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

# from infrastructure.redis import close_redis, initialize_redis  # Commented out Redis

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

    # Configure CORS - always include production origins
    allow_origins = [
        # Production
        "https://getspaced.app",
        "https://www.getspaced.app",
        "https://app.getspaced.app",
        "https://staging.getspaced.app",
        # Development
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "https://localhost:8080",
        "http://127.0.0.1:8080",
        "https://127.0.0.1:8080",
    ]

    # Add any custom origins from settings
    if settings.cors_origins:
        for origin in settings.cors_origins:
            if origin not in allow_origins:
                allow_origins.append(origin)

    print(f"CORS allowed origins: {allow_origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
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
        if settings.use_anthropic:
            if not settings.anthropic_api_key:
                logger.critical("FATAL: ANTHROPIC_API_KEY is not set. The application cannot start.")
                raise ValueError("ANTHROPIC_API_KEY is not set. Please configure your environment.")
        else:
            if not settings.openai_api_key:
                logger.critical("FATAL: OPENAI_API_KEY is not set. The application cannot start.")
                raise ValueError("OPENAI_API_KEY is not set. Please configure your environment.")

        # --- Initializations ---
        try:
            initialize_firebase()
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"ERROR: Failed to initialize Firebase: {e}")

        # try:
        #     await initialize_redis()
        #     print("Redis initialized successfully.")
        # except Exception as e:
        #     print(f"WARNING: Failed to initialize Redis: {e}")
        print("Redis initialization skipped - running without Redis")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on application shutdown."""
        # try:
        #     await close_redis()
        #     print("Redis connection closed.")
        # except Exception as e:
        #     print(f"ERROR: Failed to close Redis connection: {e}")
        print("Redis cleanup skipped - running without Redis")

    # --- Routers ---
    # The main API router for version 1
    app.include_router(api_router, prefix="/api/v1")

    # Root-level health check for Railway/load balancers
    @app.get("/health")
    async def health_check():
        """Simple health check for Railway and load balancers."""
        return {"status": "healthy", "service": "spaced-backend"}

    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        timeout_keep_alive=1,  # shorten idle connection drain
        timeout_graceful_shutdown=3,
    )
