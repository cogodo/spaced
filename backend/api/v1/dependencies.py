import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from infrastructure.firebase import get_auth
from core.monitoring.logger import get_logger

logger = get_logger("auth_dependencies")
security = HTTPBearer()

# Check if we're in development mode
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
DEV_TEST_TOKEN = "dev-test-token"
DEV_USER_UID = "dev-user-123"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate Firebase JWT token and return user info"""
    
    # Development mode bypass
    if DEVELOPMENT_MODE and credentials.credentials == DEV_TEST_TOKEN:
        logger.info("Using development mode authentication bypass")
        return {
            "uid": DEV_USER_UID,
            "email": "dev@example.com",
            "name": "Development User",
            "email_verified": True
        }
    
    try:
        # Verify the Firebase ID token
        auth_client = get_auth()
        decoded_token = auth_client.verify_id_token(credentials.credentials)
        return decoded_token
    except Exception as e:
        logger.error("Authentication failed", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        if DEVELOPMENT_MODE:
            logger.warning("Firebase auth failed in dev mode: %s", safe_error_message)
            # In development, provide helpful error message
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed. Use token '{DEV_TEST_TOKEN}' for local development, or set up Firebase credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            logger.error("Authentication failed", extra={"error_detail": safe_error_message})
            raise HTTPException(500, f"Authentication error: {safe_error_message}") 