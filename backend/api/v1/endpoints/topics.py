from fastapi import APIRouter, HTTPException, Header, Depends
from typing import List, Optional
from pydantic import BaseModel
from core.models import Topic
from core.services import TopicService, QuestionService
from api.v1.dependencies import get_current_user

router = APIRouter()


class CreateTopicRequest(BaseModel):
    name: str
    description: str


@router.post("/")
async def create_topic(
    request: CreateTopicRequest,
    current_user: dict = Depends(get_current_user)
) -> Topic:
    """Create a new topic"""
    topic_service = TopicService()
    
    try:
        topic = await topic_service.create_topic(
            user_uid=current_user.get("uid"),
            name=request.name,
            description=request.description
        )
        return topic
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create topic: {str(e)}")


@router.get("/{user_uid}")
async def get_topics(
    user_uid: str,
    current_user: dict = Depends(get_current_user)
) -> List[Topic]:
    """Get all topics for a user"""
    # Verify user can access these topics
    if current_user.get("uid") != user_uid:
        raise HTTPException(status_code=403, detail="Access denied")
    
    topic_service = TopicService()
    return await topic_service.get_user_topics(user_uid)


@router.post("/{topic_id}/generate-questions")
async def generate_questions(
    topic_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user)
):
    """Generate new questions for a topic"""
    topic_service = TopicService()
    question_service = QuestionService()
    
    # Get the topic and verify ownership
    topic = await topic_service.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    if topic.ownerUid != current_user.get("uid"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if already regenerating
    if topic.regenerating:
        return {"message": "Questions already being generated", "generatedCount": 0}
    
    try:
        # Mark as regenerating
        await topic_service.mark_regenerating(topic_id, True)
        
        # Generate questions
        questions = await question_service.generate_question_bank(topic)
        
        # Update topic with new question IDs
        question_ids = [q.id for q in questions]
        await topic_service.update_question_bank(topic_id, question_ids)
        
        return {"generatedCount": len(questions)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")
    
    finally:
        # Always mark as not regenerating
        await topic_service.mark_regenerating(topic_id, False) 