from typing import Optional, List
from google.cloud.firestore_v1 import FieldFilter
from core.models import Session, Message
from infrastructure.firebase import get_firestore_client
import uuid
from datetime import datetime


class SessionRepository:
    def __init__(self):
        self.db = get_firestore_client()

    def _get_user_sessions_collection(self, user_uid: str):
        """Get user's sessions collection reference"""
        return self.db.collection('users').document(user_uid).collection('sessions')
    
    def _get_session_messages_collection(self, user_uid: str, session_id: str):
        """Get session's messages subcollection reference"""
        return (self.db.collection('users').document(user_uid)
                .collection('sessions').document(session_id)
                .collection('messages'))

    async def create(self, session: Session) -> Session:
        """Create a new session under user's subcollection with frontend-compatible fields"""
        doc_ref = self._get_user_sessions_collection(session.userUid).document(session.id)
        
        # Check if session already exists (created by frontend)
        existing_doc = doc_ref.get()
        
        if existing_doc.exists:
            # Session already exists (created by frontend), only update backend-specific fields
            backend_updates = {
                'topicId': session.topicId,
                'questionIds': session.questionIds,
                'questionIndex': session.questionIndex,
                'responses': session.responses,
                'answeredQuestionIds': session.answeredQuestionIds,
                'currentSessionQuestionCount': session.currentSessionQuestionCount,
                'maxQuestionsPerSession': session.maxQuestionsPerSession,
                'startedAt': session.startedAt,
                'updatedAt': datetime.now(),
                'token': session.id,  # Always update token to session ID
                # Don't overwrite other frontend fields: name, state, isCompleted, messageCount, etc.
            }
            doc_ref.update(backend_updates)
            print(f"DEBUG: Updated existing session {session.id} with backend data, set token to session ID")
        else:
            # New session, create with backend-compatible fields
            session_data = session.dict()
            
            # Add frontend-required fields
            session_data['name'] = f"Learning Session - {session.startedAt.strftime('%b %d, %Y')}"
            session_data['token'] = session.id  # Use the full session ID as the token
            session_data['state'] = 'active'
            session_data['isCompleted'] = False
            session_data['messageCount'] = 0
            session_data['createdAt'] = session.startedAt
            session_data['updatedAt'] = session.startedAt
            session_data['lastMessageAt'] = None
            session_data['topics'] = []  # Will be populated by service layer
            session_data['finalScores'] = None
            
            doc_ref.set(session_data)
            print(f"DEBUG: Created new session {session.id} with backend token")
        
        return session

    async def get_by_id(self, session_id: str, user_uid: str) -> Optional[Session]:
        """Get session by ID from user's subcollection"""
        doc = self._get_user_sessions_collection(user_uid).document(session_id).get()
        if doc.exists:
            data = doc.to_dict()
            return Session.model_validate_dict(data, doc_id=session_id, user_uid=user_uid)
        return None

    async def update(self, session_id: str, user_uid: str, updates: dict) -> None:
        """Update session fields in user's subcollection"""
        doc_ref = self._get_user_sessions_collection(user_uid).document(session_id)
        doc_ref.update(updates)

    async def delete(self, session_id: str, user_uid: str) -> None:
        """Delete a session and all its messages"""
        # Delete all messages first
        messages_ref = self._get_session_messages_collection(user_uid, session_id)
        messages = messages_ref.stream()
        for message_doc in messages:
            message_doc.reference.delete()
        
        # Delete session document
        self._get_user_sessions_collection(user_uid).document(session_id).delete()

    async def list_by_user(self, user_uid: str) -> List[Session]:
        """Get all sessions for a user"""
        docs = self._get_user_sessions_collection(user_uid).stream()
        
        sessions = []
        for doc in docs:
            data = doc.to_dict()
            sessions.append(Session.model_validate_dict(data, doc_id=doc.id, user_uid=user_uid))
        
        return sessions
    
    async def list_by_user_and_topic(self, user_uid: str, topic_id: str) -> List[Session]:
        """Get sessions for a user and specific topic"""
        query = self._get_user_sessions_collection(user_uid).where(filter=FieldFilter('topicId', '==', topic_id))
        docs = query.stream()
        
        sessions = []
        for doc in docs:
            data = doc.to_dict()
            sessions.append(Session.model_validate_dict(data, doc_id=doc.id, user_uid=user_uid))
        
        # Sort by most recent first
        sessions.sort(key=lambda s: s.startedAt, reverse=True)
        return sessions

    # Message subcollection methods
    async def add_message(self, user_uid: str, session_id: str, question_id: str, 
                         question_text: str, answer_text: str, score: int) -> Message:
        """Add a message to session's messages subcollection"""
        message = Message(
            id=str(uuid.uuid4()),
            questionId=question_id,
            questionText=question_text,
            answerText=answer_text,
            score=score,
            timestamp=datetime.now()
        )
        
        doc_ref = self._get_session_messages_collection(user_uid, session_id).document(message.id)
        doc_ref.set(message.dict())
        return message

    async def get_session_messages(self, user_uid: str, session_id: str, 
                                  limit: int = 30) -> List[Message]:
        """Get messages for a session, ordered by timestamp"""
        query = (self._get_session_messages_collection(user_uid, session_id)
                .order_by('timestamp')
                .limit(limit))
        
        docs = query.stream()
        messages = []
        for doc in docs:
            data = doc.to_dict()
            messages.append(Message(**data))
        
        return messages

    async def get_message_count(self, user_uid: str, session_id: str) -> int:
        """Get total number of messages in a session"""
        messages = self._get_session_messages_collection(user_uid, session_id).stream()
        return len(list(messages)) 