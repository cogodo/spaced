from typing import List, Optional

from core.models import Topic
from infrastructure.firebase import get_firestore_client


class TopicRepository:
    def __init__(self):
        self.db = get_firestore_client()

    def _get_user_topics_collection(self, user_uid: str):
        """Get user's topics collection reference"""
        return self.db.collection("users").document(user_uid).collection("topics")

    async def create(self, topic: Topic) -> Topic:
        """Create a new topic under user's subcollection"""
        doc_ref = self._get_user_topics_collection(topic.ownerUid).document(topic.id)
        doc_ref.set(topic.dict())
        return topic

    async def get_by_id(self, topic_id: str, user_uid: str) -> Optional[Topic]:
        """Get topic by ID from user's subcollection"""
        doc = self._get_user_topics_collection(user_uid).document(topic_id).get()
        if doc.exists:
            return Topic(**doc.to_dict())
        return None

    async def list_by_owner(self, owner_uid: str) -> List[Topic]:
        """Get all topics for a user from their subcollection"""
        docs = self._get_user_topics_collection(owner_uid).stream()

        topics = []
        for doc in docs:
            topics.append(Topic(**doc.to_dict()))

        return topics

    async def update(self, topic_id: str, user_uid: str, updates: dict) -> None:
        """Update topic fields in user's subcollection"""
        doc_ref = self._get_user_topics_collection(user_uid).document(topic_id)
        doc_ref.update(updates)

    async def delete(self, topic_id: str, user_uid: str) -> None:
        """Delete a topic and all its questions"""
        # Delete all questions first
        questions_ref = (
            self._get_user_topics_collection(user_uid)
            .document(topic_id)
            .collection("questions")
        )
        questions = questions_ref.stream()
        for question_doc in questions:
            question_doc.reference.delete()

        # Delete topic document
        self._get_user_topics_collection(user_uid).document(topic_id).delete()
