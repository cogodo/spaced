import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from infrastructure.firebase import get_auth
from core.monitoring.logger import get_logger
from app.config import get_settings

logger = get_logger("auth_dependencies")
security = HTTPBearer()

settings = get_settings()
DEV_TEST_TOKEN = "dev-test-token"
DEV_USER_UID = "dev-user-123"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
            "email_verified": True
        }
    
    # Debug: Log incoming token details
    token = credentials.credentials
    logger.info(f"AUTH DEBUG: Received token (first 50 chars): {token[:50]}...")
    logger.info(f"AUTH DEBUG: Token length: {len(token)}")
    
    try:
        # Verify the Firebase ID token
        auth_client = get_auth()
        logger.info("AUTH DEBUG: Attempting to verify Firebase ID token")
        
        decoded_token = auth_client.verify_id_token(token)
        
        logger.info(f"AUTH DEBUG: Token verified successfully for user: {decoded_token.get('uid')} ({decoded_token.get('email')})")
        logger.info(f"AUTH DEBUG: Token audience: {decoded_token.get('aud')}")
        logger.info(f"AUTH DEBUG: Token issuer: {decoded_token.get('iss')}")
        
        return decoded_token
    except Exception as e:
        logger.error(f"AUTH DEBUG: Token verification failed with error: {type(e).__name__}: {str(e)}")
        logger.error("Authentication failed", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        if settings.is_development:
            logger.warning("Firebase auth failed in dev mode: %s", safe_error_message)
            # In development, provide helpful error message
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed. Use token '{DEV_TEST_TOKEN}' for local development, or set up Firebase credentials. Error: {safe_error_message}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            logger.error("Authentication failed", extra={"error_detail": safe_error_message})
            raise HTTPException(500, f"Authentication error: {safe_error_message}") 