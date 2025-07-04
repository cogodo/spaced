import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core.models import FSRSParams, Topic
from core.monitoring.logger import get_logger
from core.repositories import TopicRepository
from core.services.fsrs_service import FSRSService
from infrastructure.cache import TopicCache

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
            regenerating=False,
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

    async def update_fsrs_params(
        self,
        topic_id: str,
        user_uid: str,
        ease: float,
        interval: int,
        repetition: int,
        last_reviewed_at: datetime,
    ):
        """Update FSRS parameters and review dates for a topic using a safe read-modify-write pattern."""
        # 1. Read the full topic object first to ensure we have the complete, correct model.
        topic = await self.repository.get_by_id(topic_id, user_uid)
        if not topic:
            logger.error(f"Cannot update FSRS params: Topic {topic_id} not found for user {user_uid}")
            return

        # 2. Modify the Pydantic model in memory.
        next_review_at = last_reviewed_at + timedelta(days=interval)

        topic.fsrsParams.ease = ease
        topic.fsrsParams.interval = interval
        topic.fsrsParams.repetition = repetition
        topic.lastReviewedAt = last_reviewed_at
        topic.nextReviewAt = next_review_at

        # 3. Create the update payload from the modified model.
        # This avoids dot notation and sends a structured object, just like the working `create` method.
        update_data = {
            "fsrsParams": topic.fsrsParams.dict(),
            "lastReviewedAt": topic.lastReviewedAt,
            "nextReviewAt": topic.nextReviewAt,
        }

        await self.repository.update(topic_id, user_uid, update_data)
        self.cache.invalidate_user(user_uid)

    async def delete_topic(self, topic_id: str, user_uid: str):
        """Delete a topic and all its questions"""
        # We need to also delete all questions associated with the topic.
        # This is not yet implemented in the QuestionRepository, so we will
        # need to add it there first.
        # For now, we will just delete the topic.
        await self.repository.delete(topic_id, user_uid)
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
                    description=f"Learning topic: {topic_name}",
                )
                topics.append(new_topic)
                logger.info("Created new topic: %s for user %s", topic_name, user_uid)

        return topics

    async def get_popular_topics(self, limit: int = 6) -> List[Dict[str, str]]:
        """Get popular topics for quick-pick menu"""
        # For now, return a curated list of popular topics
        # In the future, this could be based on actual usage statistics
        popular_topics = [
            {
                "name": "Python Programming",
                "description": "Learn Python fundamentals and advanced concepts",
            },
            {
                "name": "Machine Learning",
                "description": "ML algorithms, models, and applications",
            },
            {
                "name": "Web Development",
                "description": "Frontend and backend web technologies",
            },
            {
                "name": "Data Science",
                "description": "Data analysis, statistics, and visualization",
            },
            {
                "name": "Mobile Development",
                "description": "iOS, Android, and cross-platform development",
            },
            {
                "name": "Cloud Computing",
                "description": "AWS, Azure, GCP, and cloud architectures",
            },
            {
                "name": "Database Design",
                "description": "SQL, NoSQL, and database optimization",
            },
            {
                "name": "System Design",
                "description": "Scalable systems and architecture patterns",
            },
            {
                "name": "DevOps",
                "description": "CI/CD, containerization, and infrastructure",
            },
            {
                "name": "Cybersecurity",
                "description": "Security principles and best practices",
            },
        ]

        return popular_topics[:limit]

    async def search_topics(self, query: str, user_uid: str) -> List[Topic]:
        """Search topics with fuzzy matching"""
        if not query.strip():
            return []

        topics = await self.get_user_topics(user_uid)
        if not topics:
            return []

        # Simple fuzzy matching - check if query is substring of topic name
        # (case insensitive)
        query_lower = query.lower().strip()
        matching_topics = []
        for topic in topics:
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

    async def _find_user_topic_by_name(self, user_uid: str, topic_name: str) -> List[Topic]:
        """Find a user's topic by name (case insensitive)"""
        user_topics = await self.get_user_topics(user_uid)

        matching_topics = []
        for topic in user_topics:
            if topic.name.lower() == topic_name.lower():
                matching_topics.append(topic)

        return matching_topics

    async def get_topics_with_review_status(self, user_uid: str) -> List[Dict[str, Any]]:
        """Get all topics for a user with FSRS review status"""
        fsrs_service = FSRSService()
        topics = await self.get_user_topics(user_uid)
        topics_with_status = []
        current_time = datetime.now(timezone.utc)

        for topic in topics:
            is_due = False
            is_overdue = False
            days_until_review = None
            review_urgency = "not_scheduled"

            if topic.nextReviewAt:
                time_diff = topic.nextReviewAt - current_time
                days_until_review = time_diff.days
                if time_diff.total_seconds() <= 0:
                    is_overdue = True
                    review_urgency = "overdue"
                elif days_until_review <= 1:
                    is_due = True
                    review_urgency = "due_today"
                elif days_until_review <= 3:
                    review_urgency = "due_soon"
                else:
                    review_urgency = "scheduled"

            retention_probability = None
            if topic.lastReviewedAt:
                days_since_review = (current_time - topic.lastReviewedAt).days
                retention_probability = fsrs_service.calculate_retention_probability(
                    topic.fsrsParams, days_since_review
                )

            topic_data = {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
                "questionCount": len(topic.questionBank),
                "createdAt": topic.createdAt,
                "lastReviewedAt": topic.lastReviewedAt,
                "nextReviewAt": topic.nextReviewAt,
                "isDue": is_due,
                "isOverdue": is_overdue,
                "daysUntilReview": days_until_review,
                "reviewUrgency": review_urgency,
                "retentionProbability": retention_probability,
                "fsrsParams": {
                    "ease": topic.fsrsParams.ease,
                    "interval": topic.fsrsParams.interval,
                    "repetition": topic.fsrsParams.repetition,
                },
            }
            topics_with_status.append(topic_data)

        urgency_order = {"overdue": 0, "due_today": 1, "due_soon": 2, "scheduled": 3, "not_scheduled": 4}
        topics_with_status.sort(key=lambda x: urgency_order.get(x["reviewUrgency"], 5))
        return topics_with_status

    async def get_due_topics(self, user_uid: str) -> Dict[str, Any]:
        """Get topics due for review today, categorized"""
        topics = await self.get_user_topics(user_uid)
        current_time = datetime.now(timezone.utc)
        end_of_today = current_time.replace(hour=23, minute=59, second=59)
        due_topics, overdue_topics, upcoming_topics = [], [], []

        for topic in topics:
            if not topic.nextReviewAt:
                continue
            topic_data = {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
                "questionCount": len(topic.questionBank),
                "nextReviewAt": topic.nextReviewAt,
                "fsrsParams": topic.fsrsParams.dict(),
            }
            if topic.nextReviewAt <= current_time:
                topic_data["daysOverdue"] = (current_time - topic.nextReviewAt).days
                overdue_topics.append(topic_data)
            elif topic.nextReviewAt <= end_of_today:
                due_topics.append(topic_data)
            elif topic.nextReviewAt <= current_time + timedelta(days=3):
                topic_data["daysUntil"] = (topic.nextReviewAt - current_time).days
                upcoming_topics.append(topic_data)

        overdue_topics.sort(key=lambda x: x["daysOverdue"], reverse=True)
        due_topics.sort(key=lambda x: x["nextReviewAt"])
        upcoming_topics.sort(key=lambda x: x["nextReviewAt"])

        return {
            "overdue": overdue_topics,
            "dueToday": due_topics,
            "upcoming": upcoming_topics,
            "totalDue": len(overdue_topics) + len(due_topics),
            "totalOverdue": len(overdue_topics),
            "reviewDate": current_time.isoformat(),
        }

    async def get_review_statistics(self, user_uid: str) -> Dict[str, Any]:
        """Get review statistics for a user (placeholder)."""
        logger.info("Review statistics feature is not yet implemented.")
        return {"message": "Feature coming soon: Comprehensive review statistics and insights."}
