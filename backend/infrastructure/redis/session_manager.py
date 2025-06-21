import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from infrastructure.redis.client import get_redis_client
from core.models import Session


class RedisSessionManager:
    def __init__(self, default_ttl: int = 3600):  # 1 hour default TTL
        self.default_ttl = default_ttl
        self.key_prefix = "session:"

    async def create_session(self, session_data: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """Create a new session in Redis"""
        session_id = str(uuid.uuid4())
        await self.store_session(session_id, session_data, ttl)
        return session_id

    async def store_session(self, session_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Store session data in Redis"""
        redis_client = await get_redis_client()
        key = f"{self.key_prefix}{session_id}"
        
        # Serialize datetime objects for JSON storage
        serialized_data = self._serialize_datetime_objects(session_data)
        
        # Store in Redis with TTL
        await redis_client.setex(
            key, 
            ttl or self.default_ttl, 
            json.dumps(serialized_data)
        )

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from Redis"""
        redis_client = await get_redis_client()
        key = f"{self.key_prefix}{session_id}"
        
        data = await redis_client.get(key)
        if data:
            parsed_data = json.loads(data)
            return self._deserialize_datetime_objects(parsed_data)
        return None

    async def update_session(self, session_id: str, updates: Dict[str, Any], extend_ttl: bool = True) -> bool:
        """Update specific fields in a session"""
        redis_client = await get_redis_client()
        key = f"{self.key_prefix}{session_id}"
        
        # Get current session data
        current_data = await self.get_session(session_id)
        if not current_data:
            return False
        
        # Apply updates
        current_data.update(updates)
        
        # Store updated data
        ttl = await redis_client.ttl(key) if extend_ttl else None
        if ttl and ttl > 0:
            await self.store_session(session_id, current_data, ttl)
        else:
            await self.store_session(session_id, current_data)
        
        return True

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session from Redis"""
        redis_client = await get_redis_client()
        key = f"{self.key_prefix}{session_id}"
        return bool(await redis_client.delete(key))

    async def extend_session_ttl(self, session_id: str, additional_seconds: int = None) -> bool:
        """Extend session TTL"""
        redis_client = await get_redis_client()
        key = f"{self.key_prefix}{session_id}"
        
        new_ttl = additional_seconds or self.default_ttl
        return bool(await redis_client.expire(key, new_ttl))

    async def get_session_ttl(self, session_id: str) -> Optional[int]:
        """Get remaining TTL for a session"""
        redis_client = await get_redis_client()
        key = f"{self.key_prefix}{session_id}"
        return await redis_client.ttl(key)

    async def list_user_sessions(self, user_uid: str) -> list:
        """Get all active sessions for a user (expensive operation)"""
        redis_client = await get_redis_client()
        pattern = f"{self.key_prefix}*"
        
        sessions = []
        async for key in redis_client.scan_iter(match=pattern):
            session_data = await redis_client.get(key)
            if session_data:
                data = json.loads(session_data)
                if data.get('userUid') == user_uid:
                    session_id = key.replace(self.key_prefix, '')
                    sessions.append({
                        'sessionId': session_id,
                        'data': self._deserialize_datetime_objects(data)
                    })
        
        return sessions

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (Redis handles this automatically, but useful for stats)"""
        redis_client = await get_redis_client()
        pattern = f"{self.key_prefix}*"
        
        expired_count = 0
        async for key in redis_client.scan_iter(match=pattern):
            ttl = await redis_client.ttl(key)
            if ttl == -2:  # Key doesn't exist (expired)
                expired_count += 1
        
        return expired_count

    def _serialize_datetime_objects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert datetime objects to ISO strings for JSON serialization"""
        serialized = {}
        for key, value in data.items():
            serialized[key] = self._serialize_value(value)
        return serialized

    def _serialize_value(self, value):
        """Recursively serialize datetime values, including Firestore timestamps"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif hasattr(value, 'to_datetime'):  # Firestore DatetimeWithNanoseconds
            return value.to_datetime().isoformat()
        elif hasattr(value, 'ToDatetime'):  # Alternative Firestore timestamp method
            return value.ToDatetime().isoformat()
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif hasattr(value, 'dict'):  # Pydantic models
            # Recursively serialize the dict to handle nested timestamps
            return self._serialize_value(value.dict())
        else:
            return value

    def _deserialize_datetime_objects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ISO strings back to datetime objects"""
        deserialized = {}
        for key, value in data.items():
            deserialized[key] = self._deserialize_value(value)
        return deserialized

    def _deserialize_value(self, value):
        """Recursively deserialize datetime values from ISO strings"""
        if isinstance(value, str) and self._is_iso_datetime(value):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return value
        elif isinstance(value, list):
            return [self._deserialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._deserialize_value(v) for k, v in value.items()}
        else:
            return value

    def _is_iso_datetime(self, value: str) -> bool:
        """Check if string is an ISO datetime format"""
        try:
            datetime.fromisoformat(value)
            return True
        except (ValueError, TypeError):
            return False

    # Session-specific helper methods for learning chatbot
    
    async def store_learning_session(self, session: Session) -> str:
        """Store a learning session specifically"""
        session_data = session.dict()
        return await self.create_session(session_data, ttl=7200)  # 2 hours for learning sessions

    async def get_learning_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a learning session as a Session object"""
        data = await self.get_session(session_id)
        if data:
            try:
                return Session.model_validate_dict(data)
            except Exception as e:
                print(f"Error deserializing session {session_id}: {e}")
                return None
        return None

    async def update_session_progress(self, session_id: str, question_index: int, responses: list) -> bool:
        """Update session progress"""
        return await self.update_session(session_id, {
            'questionIndex': question_index,
            'responses': [r.dict() if hasattr(r, 'dict') else r for r in responses]
        })

    async def mark_session_complete(self, session_id: str, final_score: float) -> bool:
        """Mark session as complete"""
        return await self.update_session(session_id, {
            'isComplete': True,
            'finalScore': final_score,
            'completedAt': datetime.now()
        }) 