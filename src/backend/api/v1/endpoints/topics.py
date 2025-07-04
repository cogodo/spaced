from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger
from core.services import QuestionService, TopicService

logger = get_logger("topics_api")
router = APIRouter()


@router.delete("/{topic_id}")
async def delete_topic(topic_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a topic"""
    topic_service = TopicService()

    try:
        await topic_service.delete_topic(topic_id, current_user.get("uid"))
        return {"message": "Topic deleted successfully"}
    except Exception as e:
        logger.error("Error deleting topic", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to delete topic: {safe_error_message}")


@router.get("/")
async def get_topics(view: Optional[str] = None, current_user: dict = Depends(get_current_user)) -> Any:
    """
    Get topics for the current user with different views.
    - `view=status`: (Default) All topics with detailed review status.
    - `view=due`: Topics categorized by due, overdue, and upcoming.
    - `view=stats`: User's review statistics (placeholder).
    - No view param: Returns raw list of user's topics.
    """
    topic_service = TopicService()
    user_uid = current_user.get("uid")

    try:
        if view == "status":
            return await topic_service.get_topics_with_review_status(user_uid)
        elif view == "due":
            return await topic_service.get_due_topics(user_uid)
        elif view == "stats":
            return await topic_service.get_review_statistics(user_uid)
        else:
            # Default to raw list of topics
            return await topic_service.get_user_topics(user_uid)
    except Exception as e:
        logger.error(f"Error getting topics with view '{view}'", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to get topics: {safe_error_message}")


@router.post("/{topic_id}/generate-questions")
async def generate_questions(
    topic_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user),
):
    """Generate new questions for a topic"""
    topic_service = TopicService()
    question_service = QuestionService()

    # Get the topic and verify ownership
    topic = await topic_service.get_topic(topic_id, current_user.get("uid"))
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if topic.ownerUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if already regenerating
    if topic.regenerating:
        return {"message": "Questions already being generated", "generatedCount": 0}

    try:
        # Mark as regenerating
        await topic_service.mark_regenerating(topic_id, current_user.get("uid"), True)

        # Generate questions
        questions = await question_service.generate_question_bank(topic)

        # Update topic with new question IDs
        question_ids = [q.id for q in questions]
        await topic_service.update_question_bank(topic_id, current_user.get("uid"), question_ids)

        # Mark as complete and return success
        await topic_service.mark_regenerating(topic_id, current_user.get("uid"), False)

        return {
            "message": f"Generated {len(questions)} questions",
            "questions": len(questions),
            "success": True,
            "regenerating": False,
        }

    except Exception as e:
        # Always mark as not regenerating on error
        try:
            await topic_service.mark_regenerating(topic_id, current_user.get("uid"), False)
        except Exception:
            pass  # Don't fail if cleanup fails

        logger.error("Error generating questions", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to generate questions: {safe_error_message}")
