import uuid
from typing import List, Optional, Dict, Any
from core.models import Topic, FSRSParams
from core.repositories import TopicRepository
from infrastructure.cache import TopicCache
from core.monitoring.logger import get_logger

logger = get_logger("topic_service")


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

    async def get_topic(self, topic_id: str, user_uid: str) -> Optional[Topic]:
        """Get a specific topic by ID from user's subcollection"""
        return await self.repository.get_by_id(topic_id, user_uid)

    async def mark_regenerating(self, topic_id: str, user_uid: str, regenerating: bool) -> None:
        """Mark a topic as regenerating questions"""
        await self.repository.update(topic_id, user_uid, {"regenerating": regenerating})

    async def update_question_bank(self, topic_id: str, user_uid: str, question_ids: List[str]) -> None:
        """Update the question bank for a topic"""
        await self.repository.update(topic_id, user_uid, {"questionBank": question_ids})
        # Invalidate cache since we updated the topic
        self.cache.invalidate_user(user_uid)

    # New methods for chat functionality

    async def find_or_create_topics(self, topic_names: List[str], user_uid: str) -> List[Topic]:
        """Find existing topics or create new ones from user input"""
        topics = []
        
        for topic_name in topic_names:
            topic_name = topic_name.strip()
            if not topic_name:
                continue
                
            # First, try to find existing topic for this user
            existing_topics = await self._find_user_topic_by_name(user_uid, topic_name)
            
            if existing_topics:
                # Use the first matching topic
                topics.append(existing_topics[0])
                logger.info("Found existing topic: %s for user %s", topic_name, user_uid)
            else:
                # Create new topic
                new_topic = await self.create_topic(
                    user_uid=user_uid,
                    name=topic_name,
                    description=f"Learning topic: {topic_name}"
                )
                topics.append(new_topic)
                logger.info("Created new topic: %s for user %s", topic_name, user_uid)
        
        return topics

    async def get_popular_topics(self, limit: int = 6) -> List[Dict[str, str]]:
        """Get popular topics for quick-pick menu"""
        # For now, return a curated list of popular topics
        # In the future, this could be based on actual usage statistics
        popular_topics = [
            {"name": "Python Programming", "description": "Learn Python fundamentals and advanced concepts"},
            {"name": "Machine Learning", "description": "ML algorithms, models, and applications"},
            {"name": "Web Development", "description": "Frontend and backend web technologies"},
            {"name": "Data Science", "description": "Data analysis, statistics, and visualization"},
            {"name": "Mobile Development", "description": "iOS, Android, and cross-platform development"},
            {"name": "Cloud Computing", "description": "AWS, Azure, GCP, and cloud architectures"},
            {"name": "Database Design", "description": "SQL, NoSQL, and database optimization"},
            {"name": "System Design", "description": "Scalable systems and architecture patterns"},
            {"name": "DevOps", "description": "CI/CD, containerization, and infrastructure"},
            {"name": "Cybersecurity", "description": "Security principles and best practices"}
        ]
        
        return popular_topics[:limit]

    async def search_topics(self, query: str, user_uid: str) -> List[Topic]:
        """Search topics with fuzzy matching"""
        if not query.strip():
            return []
        
        # Get all user topics
        user_topics = await self.get_user_topics(user_uid)
        
        # Simple fuzzy matching - check if query is substring of topic name (case insensitive)
        query_lower = query.lower().strip()
        matching_topics = []
        
        for topic in user_topics:
            topic_name_lower = topic.name.lower()
            topic_desc_lower = topic.description.lower()
            
            # Check for exact matches first
            if query_lower == topic_name_lower:
                matching_topics.insert(0, topic)  # Put exact matches first
            # Then partial matches in name
            elif query_lower in topic_name_lower:
                matching_topics.append(topic)
            # Then partial matches in description
            elif query_lower in topic_desc_lower:
                matching_topics.append(topic)
        
        return matching_topics

    async def validate_topics(self, topic_names: List[str], user_uid: str) -> Dict[str, Any]:
        """Validate topic names and provide suggestions"""
        valid_topics = []
        suggestions = []
        
        for topic_name in topic_names:
            topic_name = topic_name.strip()
            if not topic_name:
                continue
            
            # Check if topic exists or is close to existing topics
            search_results = await self.search_topics(topic_name, user_uid)
            
            if search_results:
                # Found exact or close match
                exact_match = any(t.name.lower() == topic_name.lower() for t in search_results)
                if exact_match:
                    valid_topics.append(topic_name)
                else:
                    # Suggest the closest match
                    suggestions.append({
                        "input": topic_name,
                        "suggestion": search_results[0].name,
                        "type": "existing_topic"
                    })
            else:
                # No match found, topic will be created
                valid_topics.append(topic_name)
        
        return {
            "valid_topics": valid_topics,
            "suggestions": suggestions,
            "has_errors": len(suggestions) > 0
        }

    async def _find_user_topic_by_name(self, user_uid: str, topic_name: str) -> List[Topic]:
        """Find a user's topic by name (case insensitive)"""
        user_topics = await self.get_user_topics(user_uid)
        
        matching_topics = []
        for topic in user_topics:
            if topic.name.lower() == topic_name.lower():
                matching_topics.append(topic)
        
        return matching_topics 