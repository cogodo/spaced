from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from api.v1.router import api_router
from api.health import router as health_router
from infrastructure.firebase import initialize_firebase
from infrastructure.redis import initialize_redis, close_redis


def create_app() -> FastAPI:
    app = FastAPI(
        title="Learning Chatbot API",
        description="Spaced repetition learning chatbot with Firebase integration",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup"""
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