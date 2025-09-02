import asyncio
import uuid
from typing import Optional, Tuple

from core.models import Message, Question
from core.models.session import Session, SessionState, TurnState
from core.monitoring.logger import get_logger
from core.repositories.session_repository import SessionRepository
from core.services.question_service import QuestionService
from core.services.topic_service import TopicService

logger = get_logger(__name__)


class SessionServiceError(Exception):
    """Base exception for SessionService errors."""

    pass


class SessionService:
    """
    Unified session service that replaces ContextService.
    Manages both learning logic and UI state in a single sessions collection.
    """

    def __init__(self):
        self.repository = SessionRepository()
        self.question_service = QuestionService()
        self.topic_service = TopicService()

    async def start_session(
        self, user_uid: str, topic_id: str, session_id: Optional[str] = None, topics: list = None, name: str = None
    ) -> Session:
        """Starts a new unified learning session."""
        logger.info(f"Starting session for user {user_uid} and topic {topic_id}")
        try:
            # Prefer the topic's pre-built question bank using a local cursor
            topic = await self.topic_service.get_topic(topic_id, user_uid)
            question_ids = []

            if topic and topic.questionBank:
                start_idx = max(0, min(topic.questionCursor or 0, len(topic.questionBank)))
                end_idx = min(start_idx + 5, len(topic.questionBank))
                question_ids = topic.questionBank[start_idx:end_idx]

                # If not enough questions, regenerate and append then retry slice
                if len(question_ids) < 5:
                    logger.info(
                        f"Not enough questions in bank ({len(topic.questionBank)}). Regenerating for topic {topic_id}..."
                    )
                    try:
                        await self.topic_service.mark_regenerating(topic_id, user_uid, True)
                        new_questions = await self.question_service.generate_question_bank(topic)
                        if new_questions:
                            # Append new IDs to topic bank
                            topic.questionBank.extend([q.id for q in new_questions])
                            # Persist updated bank
                            await self.topic_service.update_question_bank(topic_id, user_uid, topic.questionBank)
                        logger.info(
                            f"Appended {len(new_questions) if new_questions else 0} new questions to topic {topic_id}"
                        )
                    finally:
                        await self.topic_service.mark_regenerating(topic_id, user_uid, False)

                    # Recompute slice after regeneration
                    end_idx = min(start_idx + 5, len(topic.questionBank))
                    question_ids = topic.questionBank[start_idx:end_idx]

                # Advance cursor by the number we actually took
                new_cursor = start_idx + len(question_ids)
                if new_cursor != (topic.questionCursor or 0):
                    try:
                        self.topic_service.repository.update(topic_id, user_uid, {"questionCursor": new_cursor})
                        logger.info(
                            f"Advanced question cursor for topic {topic_id} from {topic.questionCursor or 0} to {new_cursor}"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update questionCursor for topic {topic_id}: {e}")

            # Fallback if no topic/bank available: sample diverse questions
            if not question_ids:
                attempts = 5
                for attempt in range(attempts):
                    questions = self.question_service.get_diverse_questions(topic_id, user_uid, limit=5)
                    if questions:
                        question_ids = [q.id for q in questions]
                        break
                    if attempt < attempts - 1:
                        await asyncio.sleep(0.25)

            session_id = session_id or str(uuid.uuid4())
            session = Session(
                id=session_id,
                userUid=user_uid,
                name=name or f"Session - {session_id[:8]}",
                topics=topics or [],
                topicId=topic_id,
                questionIds=question_ids,
                state=SessionState.ACTIVE,
                turnState=TurnState.AWAITING_INITIAL_ANSWER,
            )

            self.repository.create(session)
            logger.info(f"Session {session.id} created successfully.")
            return session
        except Exception as e:
            raise SessionServiceError(f"Failed to start session for topic {topic_id}") from e

    def get_session(self, session_id: str, user_uid: str) -> Optional[Session]:
        """Retrieves a session by its ID."""
        return self.repository.get(session_id, user_uid)

    def get_current_question(self, session_id: str, user_uid: str) -> Tuple[Optional[Session], Optional[Question]]:
        """Gets the current question for a given session."""
        try:
            session = self.get_session(session_id, user_uid)
            if not session or session.questionIdx >= len(session.questionIds):
                return session, None

            question_id = session.questionIds[session.questionIdx]
            question = self.question_service.get_question(question_id, user_uid, session.topicId)
            return session, question
        except Exception as e:
            raise SessionServiceError(f"Failed to get current question for session {session_id}") from e

    def add_message_to_session(self, session_id: str, user_uid: str, message: Message) -> None:
        """Append a single message to session's messages and update session metadata."""
        try:
            # Append the message
            self.repository.append_messages(session_id, user_uid, [message])

            # Update session counters/lastMessageAt
            session = self.get_session(session_id, user_uid)
            if not session:
                return

            new_count = (session.messageCount or 0) + 1
            updates = {
                "messageCount": new_count,
                "lastMessageAt": message.timestamp,
                "updatedAt": message.timestamp,
            }
            self.repository.update(session_id, user_uid, updates)
        except Exception as e:
            raise SessionServiceError(f"Failed to append message to session {session_id} for user {user_uid}") from e

    def record_answer(self, session_id: str, user_uid: str, score: int) -> Session:
        """Records a user's answer score and advances to the next question."""
        session = self.get_session(session_id, user_uid)
        if not session:
            raise ValueError("Session not found")

        current_question_id = session.questionIds[session.questionIdx]
        session.scores[current_question_id] = score
        session.questionIdx += 1
        session.touch()

        self.repository.update(session_id, user_uid, session.dict())
        return session

    def update_session_state(self, session_id: str, user_uid: str, **updates) -> Session:
        """Update session fields."""
        session = self.get_session(session_id, user_uid)
        if not session:
            raise ValueError("Session not found")

        # Update the session object
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.touch()

        # Save to database
        self.repository.update(session_id, user_uid, session.dict())
        return session

    # Backward compatibility methods for existing ContextService interface
    async def start_context(self, user_uid: str, topic_id: str, context_id: Optional[str] = None) -> Session:
        """Backward compatibility wrapper for start_session."""
        logger.warning("start_context is deprecated, use start_session instead")
        return await self.start_session(user_uid, topic_id, context_id)

    async def get_context(self, context_id: str, user_uid: str) -> Optional[Session]:
        """Backward compatibility wrapper for get_session."""
        logger.warning("get_context is deprecated, use get_session instead")
        return await self.get_session(context_id, user_uid)


# Backward compatibility alias
ContextService = SessionService
