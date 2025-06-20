import uuid
from typing import List, Optional
from core.models import Topic, FSRSParams
from core.repositories import TopicRepository
from infrastructure.cache import TopicCache


class TopicService:
    def __init__(self):
        self.repository = TopicRepository()
        self.cache = TopicCache()

    async def get_user_topics(self, user_uid: str) -> List[Topic]:
        """Get all topics for a user with caching"""
        # Try cache first
        cached_topics = self.cache.get_topics(user_uid)
        if cached_topics is not None:
            return cached_topics
        
        # Fetch from database
        topics = await self.repository.list_by_owner(user_uid)
        
        # Cache the results
        self.cache.set_topics(user_uid, topics)
        
        return topics

    async def create_topic(self, user_uid: str, name: str, description: str) -> Topic:
        """Create a new topic for a user"""
        topic = Topic(
            id=str(uuid.uuid4()),
            ownerUid=user_uid,
            name=name,
            description=description,
            questionBank=[],
            fsrsParams=FSRSParams(),
            regenerating=False
        )
        
        created_topic = await self.repository.create(topic)
        
        # Invalidate cache
        self.cache.invalidate_user(user_uid)
        
        return created_topic

    async def get_topic(self, topic_id: str) -> Optional[Topic]:
        """Get a specific topic by ID"""
        return await self.repository.get_by_id(topic_id)

    async def mark_regenerating(self, topic_id: str, regenerating: bool) -> None:
        """Mark a topic as regenerating questions"""
        await self.repository.update(topic_id, {"regenerating": regenerating})

    async def update_question_bank(self, topic_id: str, question_ids: List[str]) -> None:
        """Update the question bank for a topic"""
        await self.repository.update(topic_id, {"questionBank": question_ids})
        # Note: Could also invalidate specific user cache here if needed 