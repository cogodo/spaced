from typing import List, Optional
from core.models import Question
from infrastructure.firebase import get_firestore_client


class QuestionRepository:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection('questions')

    async def create(self, question: Question) -> Question:
        """Create a new question in Firestore"""
        doc_ref = self.collection.document(question.id)
        doc_ref.set(question.dict())
        return question

    async def get_by_id(self, question_id: str) -> Optional[Question]:
        """Get question by ID"""
        doc = self.collection.document(question_id).get()
        if doc.exists:
            return Question(**doc.to_dict())
        return None

    async def list_by_topic(self, topic_id: str) -> List[Question]:
        """Get all questions for a topic"""
        query = self.collection.where('topicId', '==', topic_id)
        docs = query.stream()
        
        questions = []
        for doc in docs:
            questions.append(Question(**doc.to_dict()))
        
        return questions

    async def update(self, question_id: str, updates: dict) -> None:
        """Update question fields"""
        doc_ref = self.collection.document(question_id)
        doc_ref.update(updates)

    async def delete(self, question_id: str) -> None:
        """Delete a question"""
        self.collection.document(question_id).delete()

    async def delete_by_topic(self, topic_id: str) -> None:
        """Delete all questions for a topic"""
        query = self.collection.where('topicId', '==', topic_id)
        docs = query.stream()
        
        for doc in docs:
            doc.reference.delete()

    async def create_batch(self, questions: List[Question]) -> None:
        """Create multiple questions in a batch"""
        batch = self.db.batch()
        for question in questions:
            doc_ref = self.collection.document(question.id)
            batch.set(doc_ref, question.dict())
        batch.commit() 