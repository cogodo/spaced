from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query

from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger
from core.services import QuestionService, TopicService

logger = get_logger("topics_api")
router = APIRouter()


class TopicAction(str, Enum):
    GENERATE_QUESTIONS = "generate_questions"


@router.get("/")
async def get_topics(
    topic_id: Optional[str] = Query(None, description="ID of a specific topic to fetch."),
    view: Optional[str] = Query(None, description="The view to return: `status`, `due`, or `stats`."),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """
    Get topics for the current user.

    Can fetch a list of topics with different views or a single topic by its ID.
    """
    topic_service = TopicService()
    user_uid = current_user.get("uid")

    try:
        # --- Handle single topic request ---
        if topic_id:
            if view == "status":
                logger.info(f"Getting topic {topic_id} with review status for user {user_uid}")
                topic_with_status = await topic_service.get_topic_with_review_status(topic_id, user_uid)
                if not topic_with_status:
                    raise HTTPException(status_code=404, detail="Topic not found")
                return topic_with_status
            else:
                logger.info(f"Getting topic {topic_id} for user {user_uid}")
                topic = await topic_service.get_topic(topic_id, user_uid)
                if not topic:
                    raise HTTPException(status_code=404, detail="Topic not found")
                return topic

        # --- Handle topic list request ---
        logger.info(f"Getting topics with view '{view}' for user {user_uid}")
        if view == "status":
            return await topic_service.get_topics_with_review_status(user_uid)
        elif view == "due":
            return await topic_service.get_due_topics(user_uid)
        elif view == "stats":
            return await topic_service.get_review_statistics(user_uid)
        else:
            # Default to a simple list of topics
            return await topic_service.get_user_topics(user_uid)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting topics", extra={"error_detail": str(e), "topic_id": topic_id, "view": view})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to get topics: {safe_error_message}")


@router.delete("/{topic_id}", status_code=204)
async def delete_topic_endpoint(
    topic_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Deletes a topic and all its associated questions.
    """
    topic_service = TopicService()
    user_uid = current_user.get("uid")

    try:
        # Verify topic exists and belongs to the user before deleting
        topic = await topic_service.get_topic(topic_id, user_uid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        await topic_service.delete_topic(topic_id, user_uid)
        return

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting topic", extra={"error_detail": str(e), "topic_id": topic_id})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to delete topic: {safe_error_message}")


@router.post("/{topic_id}")
async def manage_topic(
    topic_id: str,
    action: TopicAction = Body(..., description="Action to perform on the topic"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user),
):
    """Manage a topic by performing actions like generating questions or deleting."""

    if action == TopicAction.GENERATE_QUESTIONS:
        return await generate_questions(topic_id, current_user, idempotency_key)

    else:
        raise HTTPException(400, "Invalid action specified")


async def generate_questions(topic_id: str, current_user: dict, idempotency_key: Optional[str] = None):
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
