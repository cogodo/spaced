import time
from typing import Dict, List, Optional

from core.models import Topic


class TopicCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, List[Topic]] = {}
        self._expires: Dict[str, float] = {}
        self._ttl_seconds = ttl_seconds

    def get_topics(self, user_uid: str) -> Optional[List[Topic]]:
        """Get topics from cache if not expired, otherwise return None"""
        now = time.time()
        if user_uid in self._cache and self._expires.get(user_uid, 0) > now:
            return self._cache[user_uid]
        return None

    def set_topics(self, user_uid: str, topics: List[Topic]) -> None:
        """Store topics in cache with TTL"""
        now = time.time()
        self._cache[user_uid] = topics
        self._expires[user_uid] = now + self._ttl_seconds

    def invalidate_user(self, user_uid: str) -> None:
        """Remove user's topics from cache"""
        self._cache.pop(user_uid, None)
        self._expires.pop(user_uid, None)

    def clear(self) -> None:
        """Clear entire cache"""
        self._cache.clear()
        self._expires.clear()
