from typing import List, Optional
from core.models import Topic
from infrastructure.firebase import get_firestore_client


class TopicRepository:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection('topics')

    async def create(self, topic: Topic) -> Topic:
        """Create a new topic in Firestore"""
        doc_ref = self.collection.document(topic.id)
        doc_ref.set(topic.dict())
        return topic

    async def get_by_id(self, topic_id: str) -> Optional[Topic]:
        """Get topic by ID"""
        doc = self.collection.document(topic_id).get()
        if doc.exists:
            return Topic(**doc.to_dict())
        return None

    async def list_by_owner(self, owner_uid: str) -> List[Topic]:
        """Get all topics for a user"""
        query = self.collection.where('ownerUid', '==', owner_uid)
        docs = query.stream()
        
        topics = []
        for doc in docs:
            topics.append(Topic(**doc.to_dict()))
        
        return topics

    async def update(self, topic_id: str, updates: dict) -> None:
        """Update topic fields"""
        doc_ref = self.collection.document(topic_id)
        doc_ref.update(updates)

    async def delete(self, topic_id: str) -> None:
        """Delete a topic"""
        self.collection.document(topic_id).delete() 