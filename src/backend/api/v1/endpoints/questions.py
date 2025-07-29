import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from api.v1.dependencies import get_current_user
from core.models.question import CreateQuestionsRequest, Question, UpdateQuestionRequest
from core.monitoring.logger import get_logger
from core.services import QuestionService, TopicService

logger = get_logger("questions_api")
router = APIRouter()


@router.get("/topics/{topic_id}/questions", response_model=List[Question])
async def get_topic_questions(
    topic_id: str,
    limit: Optional[int] = None,
    randomize: bool = False,
    current_user: dict = Depends(get_current_user),
) -> List[Question]:
    """Get questions for a topic with optional randomization and limiting."""
    user_uid = current_user.get("uid")
    question_service = QuestionService()
    topic_service = TopicService()

    try:
        # Verify topic exists and belongs to the user
        topic = await topic_service.get_topic(topic_id, user_uid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Get questions for the topic
        questions = question_service.get_topic_questions(topic_id, user_uid, limit=limit, randomize=randomize)
        logger.info(
            f"Retrieved {len(questions)} questions for topic {topic_id} for user {user_uid} (randomized: {randomize}, limit: {limit})"
        )
        return questions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting topic questions", extra={"error_detail": str(e), "topic_id": topic_id, "user_uid": user_uid}
        )
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to get topic questions: {safe_error_message}")


@router.post("/topics/{topic_id}/questions", response_model=List[Question])
async def create_questions(
    topic_id: str,
    request: CreateQuestionsRequest,
    current_user: dict = Depends(get_current_user),
) -> List[Question]:
    """Create multiple questions for a topic."""
    user_uid = current_user.get("uid")
    question_service = QuestionService()
    topic_service = TopicService()

    try:
        # Verify topic exists and belongs to the user
        topic = await topic_service.get_topic(topic_id, user_uid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Create questions
        created_questions = []
        for question_request in request.questions:
            question = Question(
                id=str(uuid.uuid4()),
                topicId=topic_id,
                text=question_request.text,
                type=question_request.type,
                difficulty=question_request.difficulty,
                metadata={
                    "generated_by": "user",
                    "created_at": str(datetime.utcnow()),
                },
            )
            created_question = question_service.repository.create(question, user_uid)
            created_questions.append(created_question)

        # Update topic's question bank
        existing_questions = question_service.get_topic_questions(topic_id, user_uid)
        question_ids = [q.id for q in existing_questions]
        await topic_service.update_question_bank(topic_id, user_uid, question_ids)

        logger.info(f"Created {len(created_questions)} questions for topic {topic_id} for user {user_uid}")
        return created_questions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating questions", extra={"error_detail": str(e), "topic_id": topic_id, "user_uid": user_uid}
        )
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to create questions: {safe_error_message}")


@router.delete("/topics/{topic_id}/questions/{question_id}", status_code=204)
async def delete_question(
    topic_id: str,
    question_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a specific question from a topic."""
    user_uid = current_user.get("uid")
    question_service = QuestionService()
    topic_service = TopicService()

    try:
        # Verify topic exists and belongs to the user
        topic = await topic_service.get_topic(topic_id, user_uid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Verify question exists and belongs to the topic
        question = question_service.repository.get_by_id(question_id, user_uid, topic_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Delete the question
        question_service.repository.delete(question_id, user_uid, topic_id)

        # Update topic's question bank
        remaining_questions = question_service.get_topic_questions(topic_id, user_uid)
        question_ids = [q.id for q in remaining_questions]
        await topic_service.update_question_bank(topic_id, user_uid, question_ids)

        logger.info(f"Deleted question {question_id} from topic {topic_id} for user {user_uid}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting question",
            extra={"error_detail": str(e), "topic_id": topic_id, "question_id": question_id, "user_uid": user_uid},
        )
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to delete question: {safe_error_message}")


@router.put("/topics/{topic_id}/questions/{question_id}", response_model=Question)
async def update_question(
    topic_id: str,
    question_id: str,
    question_update: UpdateQuestionRequest,
    current_user: dict = Depends(get_current_user),
) -> Question:
    """Update a specific question in a topic."""
    user_uid = current_user.get("uid")
    question_service = QuestionService()
    topic_service = TopicService()

    try:
        # Verify topic exists and belongs to the user
        topic = await topic_service.get_topic(topic_id, user_uid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Verify question exists and belongs to the topic
        existing_question = question_service.repository.get_by_id(question_id, user_uid, topic_id)
        if not existing_question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Update the question
        updates = {
            "text": question_update.text,
            "type": question_update.type,
            "difficulty": question_update.difficulty,
        }
        question_service.repository.update(question_id, user_uid, topic_id, updates)

        # Get the updated question
        updated_question = question_service.repository.get_by_id(question_id, user_uid, topic_id)
        logger.info(f"Updated question {question_id} in topic {topic_id} for user {user_uid}")
        return updated_question

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating question",
            extra={"error_detail": str(e), "topic_id": topic_id, "question_id": question_id, "user_uid": user_uid},
        )
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to update question: {safe_error_message}")
