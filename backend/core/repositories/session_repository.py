from typing import Optional, List
from core.models import Session
from infrastructure.firebase import get_firestore_client


class SessionRepository:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection('sessions')

    async def create(self, session: Session) -> Session:
        """Create a new session in Firestore"""
        doc_ref = self.collection.document(session.id)
        doc_ref.set(session.dict())
        return session

    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        doc = self.collection.document(session_id).get()
        if doc.exists:
            data = doc.to_dict()
            # Handle datetime strings from Firestore
            return Session.model_validate_dict(data)
        return None

    async def update(self, session_id: str, updates: dict) -> None:
        """Update session fields"""
        doc_ref = self.collection.document(session_id)
        doc_ref.update(updates)

    async def delete(self, session_id: str) -> None:
        """Delete a session"""
        self.collection.document(session_id).delete()

    async def list_by_user(self, user_uid: str) -> List[Session]:
        """Get all sessions for a user"""
        query = self.collection.where('userUid', '==', user_uid)
        docs = query.stream()
        
        sessions = []
        for doc in docs:
            data = doc.to_dict()
            sessions.append(Session.model_validate_dict(data))
        
        return sessions 