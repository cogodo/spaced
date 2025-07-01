from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from core.monitoring.logger import get_logger
from infrastructure.firebase import get_auth

logger = get_logger("auth_dependencies")
security = HTTPBearer()

settings = get_settings()
DEV_TEST_TOKEN = "dev-test-token"
DEV_USER_UID = "dev-user-123"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Validate Firebase JWT token and return user info"""

    # Debug: Log development mode detection
    logger.info(f"AUTH DEBUG: settings.is_development = {settings.is_development}")
    logger.info(f"AUTH DEBUG: credentials.credentials = '{credentials.credentials}'")
    logger.info(f"AUTH DEBUG: DEV_TEST_TOKEN = '{DEV_TEST_TOKEN}'")
    logger.info(f"AUTH DEBUG: Token match = {credentials.credentials == DEV_TEST_TOKEN}")

    # Development mode bypass
    if settings.is_development and credentials.credentials == DEV_TEST_TOKEN:
        logger.info("Using development mode authentication bypass")
        return {
            "uid": DEV_USER_UID,
            "email": "dev@example.com",
            "name": "Development User",
            "email_verified": True,
        }

    # Debug: Log incoming token details
    token = credentials.credentials
    logger.info(f"AUTH DEBUG: Received token (first 50 chars): {token[:50]}...")
    logger.info(f"AUTH DEBUG: Token length: {len(token)}")

    try:
        # Verify the token against Firebase
        auth = get_auth()
        decoded_token = auth.verify_id_token(token)
        logger.info(
            f"AUTH DEBUG: Token verified successfully for user: "
            f"{decoded_token.get('uid')} ({decoded_token.get('email')})"
        )
        logger.info(f"AUTH DEBUG: Token audience: {decoded_token.get('aud')}")
        return decoded_token
    except auth.InvalidIdTokenError as e:
        logger.error(f"AUTH DEBUG: Invalid ID token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"AUTH DEBUG: Token verification failed with error: {type(e).__name__}: {str(e)}")
        logger.error("Authentication failed", extra={"error_detail": str(e)})

        # Sanitize error message for production
        safe_error_message = str(e) if settings.environment == "development" else "Internal server error"
        if settings.environment == "development":
            detail_message = (
                f"Authentication failed. Use token '{DEV_TEST_TOKEN}' for local "
                f"development, or set up Firebase credentials. Error: "
                f"{safe_error_message}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail_message,
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
