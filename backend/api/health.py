from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Simple health check to verify service is up"""
    return {"status": "ok"}


@router.get("/healthz")
async def health_check_detailed():
    """Detailed health check for kubernetes liveness probe"""
    return {"status": "healthy", "version": "1.0.0"}
