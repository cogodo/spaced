from typing import List, Optional

from core.models import Question
from infrastructure.firebase import get_firestore_client


class QuestionRepository:
    def __init__(self):
        self.db = get_firestore_client()

    def _get_topic_questions_collection(self, user_uid: str, topic_id: str):
        """Get topic's questions collection reference"""
        return (
            self.db.collection("users")
            .document(user_uid)
            .collection("topics")
            .document(topic_id)
            .collection("questions")
        )

    async def create(self, question: Question, user_uid: str) -> Question:
        """Create a new question under topic's subcollection"""
        doc_ref = self._get_topic_questions_collection(user_uid, question.topicId).document(question.id)
        doc_ref.set(question.dict())
        return question

    async def get_by_id(self, question_id: str, user_uid: str, topic_id: str) -> Optional[Question]:
        """Get question by ID from topic's subcollection"""
        doc = self._get_topic_questions_collection(user_uid, topic_id).document(question_id).get()
        if doc.exists:
            return Question(**doc.to_dict())
        return None

    async def list_by_topic(self, topic_id: str, user_uid: str, limit: int = 50) -> List[Question]:
        """Get questions for a topic, paginated for efficiency"""
        query = self._get_topic_questions_collection(user_uid, topic_id).limit(limit)
        docs = query.stream()

        questions = []
        for doc in docs:
            questions.append(Question(**doc.to_dict()))

        return questions

    async def update(self, question_id: str, user_uid: str, topic_id: str, updates: dict) -> None:
        """Update question fields in topic's subcollection"""
        doc_ref = self._get_topic_questions_collection(user_uid, topic_id).document(question_id)
        doc_ref.update(updates)

    async def delete(self, question_id: str, user_uid: str, topic_id: str) -> None:
        """Delete a question from topic's subcollection"""
        self._get_topic_questions_collection(user_uid, topic_id).document(question_id).delete()

    async def delete_by_topic(self, topic_id: str, user_uid: str) -> None:
        """Delete all questions for a topic"""
        docs = self._get_topic_questions_collection(user_uid, topic_id).stream()

        for doc in docs:
            doc.reference.delete()

    async def create_batch(self, questions: List[Question], user_uid: str) -> None:
        """Create multiple questions in a batch"""
        batch = self.db.batch()
        for question in questions:
            doc_ref = self._get_topic_questions_collection(user_uid, question.topicId).document(question.id)
            batch.set(doc_ref, question.dict())
        batch.commit()
