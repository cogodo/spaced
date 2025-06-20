import redis.asyncio as redis
from app.config import settings
from typing import Optional


_redis_client: Optional[redis.Redis] = None


async def initialize_redis() -> Optional[redis.Redis]:
    """Initialize Redis client"""
    global _redis_client
    
    # Check if Redis is configured
    if not settings.redis_url:
        print("Redis is not configured - skipping Redis initialization")
        return None
    
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,  # Automatically decode responses to strings
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True
        )
        
        # Test connection
        try:
            await _redis_client.ping()
            print("Redis connected successfully")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            _redis_client = None
            raise
    
    return _redis_client


async def get_redis_client() -> redis.Redis:
    """Get Redis client, initializing if needed"""
    if _redis_client is None:
        return await initialize_redis()
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None 