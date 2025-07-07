import uuid
from typing import Optional, Tuple

from core.models import Question
from core.models.context import Context
from core.monitoring.logger import get_logger
from core.repositories.context_repository import ContextRepository
from core.services.question_service import QuestionService

logger = get_logger(__name__)


class ContextServiceError(Exception):
    """Base exception for ContextService errors."""

    pass


class ContextService:
    def __init__(self):
        self.repository = ContextRepository()
        self.question_service = QuestionService()

    async def start_context(self, user_uid: str, topic_id: str, context_id: Optional[str] = None) -> Context:
        """Starts a new learning context (chat session)."""
        logger.info(f"Starting context for user {user_uid} and topic {topic_id}")
        try:
            questions = await self.question_service.get_topic_questions(topic_id, user_uid)
            if not questions:
                logger.warning(f"No questions found for topic {topic_id}. Starting with empty context.")
                question_ids = []
            else:
                question_ids = [q.id for q in questions]

            context = Context(
                chatId=context_id or str(uuid.uuid4()),
                userUid=user_uid,
                topicId=topic_id,
                questionIds=question_ids,
            )
            await self.repository.create(context)
            logger.info(f"Context {context.chatId} created successfully.")
            return context
        except Exception as e:
            raise ContextServiceError(f"Failed to start context for topic {topic_id}") from e

    async def get_context(self, context_id: str, user_uid: str) -> Optional[Context]:
        """Retrieves a context by its ID."""
        return await self.repository.get(context_id, user_uid)

    async def get_current_question(
        self, context_id: str, user_uid: str
    ) -> Tuple[Optional[Context], Optional[Question]]:
        """Gets the current question for a given context."""
        try:
            context = await self.get_context(context_id, user_uid)
            if not context or context.questionIdx >= len(context.questionIds):
                return context, None

            question_id = context.questionIds[context.questionIdx]
            question = await self.question_service.get_question(question_id, user_uid, context.topicId)
            return context, question
        except Exception as e:
            raise ContextServiceError(f"Failed to get current question for context {context_id}") from e

    async def record_answer(self, context_id: str, user_uid: str, score: int) -> Context:
        """Records a user's answer score and advances to the next question."""
        context = await self.get_context(context_id, user_uid)
        if not context:
            raise ValueError("Context not found")

        current_question_id = context.questionIds[context.questionIdx]
        context.scores[current_question_id] = score
        context.questionIdx += 1
        context.touch()

        await self.repository.update(context_id, user_uid, context.dict())
        return context
