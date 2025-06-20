from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio

# Import centralized API router
from api.v1.router import api_router
from api.monitoring import router as monitoring_router

# Import services and configs
from infrastructure.firebase import initialize_firebase
from app.config import get_settings
from core.monitoring.logger import setup_logging, get_logger
from core.monitoring.performance import start_performance_monitoring

# Import middleware
from middleware.performance import PerformanceMiddleware, RequestSizeLimitMiddleware
from middleware.rate_limiting import RateLimitMiddleware, get_rate_limiter
from middleware.logging import LoggingMiddleware, SecurityLoggingMiddleware

# Import reliability components
from core.reliability.circuit_breaker import CircuitBreakerConfig, get_circuit_breaker
from core.reliability.retry import RetryConfig

logger = get_logger("main")

# Initialize settings
settings = get_settings()

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="Learning Chatbot API",
    description="AI-powered spaced repetition learning system with production monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup logging first
setup_logging(log_level=settings.log_level, use_json=True)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with proper logging"""
    logger.error("Unhandled exception occurred",
                method=request.method,
                path=str(request.url.path),
                error_type=type(exc).__name__,
                error_message=str(exc),
                stack_trace=str(exc))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware in correct order
# 1. Security logging (first to catch suspicious requests)
app.middleware("http")(SecurityLoggingMiddleware())

# 2. Request size limiting
app.middleware("http")(RequestSizeLimitMiddleware(max_size_mb=10.0))

# 3. Rate limiting
rate_limiter = get_rate_limiter()
app.middleware("http")(RateLimitMiddleware(rate_limiter))

# 4. Performance tracking and logging
app.middleware("http")(PerformanceMiddleware())

# 5. Detailed request/response logging (last for complete context)
app.middleware("http")(LoggingMiddleware(
    log_requests=True,
    log_responses=True,
    log_request_body=False,  # Don't log bodies in production for security
    log_response_body=False,
    max_body_size=1024
))

# Health check endpoint (before auth)
@app.get("/health", tags=["health"])
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "service": "learning_chatbot_api"}

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(monitoring_router)

# Circuit breakers for external services
openai_circuit_breaker = get_circuit_breaker(
    "openai_service",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=15.0
    )
)

firebase_circuit_breaker = get_circuit_breaker(
    "firebase_service", 
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        success_threshold=3,
        timeout=10.0
    )
)

redis_circuit_breaker = get_circuit_breaker(
    "redis_service",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=5.0
    )
)

@app.on_event("startup")
async def startup_event():
    """Initialize services and monitoring on startup"""
    logger.info("Starting Learning Chatbot API...",
               environment=settings.environment,
               debug=settings.debug)
    
    try:
        # Initialize Firebase
        logger.info("Initializing Firebase...")
        initialize_firebase()
        logger.info("Firebase initialized successfully")
        
        # Start performance monitoring
        logger.info("Starting performance monitoring...")
        start_performance_monitoring()
        logger.info("Performance monitoring started")
        
        # Log startup completion
        logger.info("Learning Chatbot API startup completed",
                   features_enabled=[
                       "structured_logging",
                       "performance_monitoring", 
                       "rate_limiting",
                       "circuit_breakers",
                       "security_logging",
                       "metrics_collection",
                       "chat_api"  # New chat API feature
                   ])
        
    except Exception as e:
        logger.error("Failed to initialize application",
                    error_type=type(e).__name__,
                    error_message=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Learning Chatbot API...")
    
    try:
        # Stop performance monitoring
        from core.monitoring.performance import get_performance_tracker
        perf_tracker = get_performance_tracker()
        perf_tracker.stop_monitoring()
        
        logger.info("Learning Chatbot API shutdown completed")
        
    except Exception as e:
        logger.error("Error during shutdown",
                    error_type=type(e).__name__,
                    error_message=str(e))

# Enhanced root endpoint with system info
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Learning Chatbot API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "monitoring": "/monitoring/status",
        "chat_api": "/api/v1/chat",  # New chat API
        "features": {
            "spaced_repetition": "FSRS algorithm",
            "ai_question_generation": "OpenAI GPT-3.5",
            "intelligent_scoring": "LLM-powered evaluation",
            "session_management": "Redis + Firebase",
            "monitoring": "Comprehensive observability",
            "reliability": "Circuit breakers + retries",
            "security": "Rate limiting + logging",
            "chat_interface": "Chat-compatible API endpoints"  # New feature
        }
    }

if __name__ == "__main__":
    # Enhanced uvicorn configuration for production readiness
    uvicorn.run(
        "main:app",
        host=settings.host,  # Use config values
        port=settings.port,  # Use config values
        reload=settings.debug,
        log_level="info",
        access_log=True,
        # Production settings
        workers=1 if settings.debug else 4,
        loop="uvloop" if not settings.debug else "asyncio",
        # Timeout settings
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30,
        # Security settings
        server_header=False,
        date_header=False
    ) 