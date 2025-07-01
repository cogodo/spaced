from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from api.v1.dependencies import get_current_user
from core.models import Topic
from core.monitoring.logger import get_logger
from core.services import QuestionService, TopicService
from core.services.fsrs_service import FSRSService

logger = get_logger("topics_api")
router = APIRouter()


class CreateTopicRequest(BaseModel):
    name: str
    description: str


@router.post("/")
async def create_topic(request: CreateTopicRequest, current_user: dict = Depends(get_current_user)) -> Topic:
    """Create a new topic"""
    topic_service = TopicService()

    try:
        topic = await topic_service.create_topic(
            user_uid=current_user.get("uid"),
            name=request.name,
            description=request.description,
        )
        return topic
    except Exception as e:
        logger.error("Error creating topic", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to create topic: {safe_error_message}")


@router.get("/{user_uid}")
async def get_topics(user_uid: str, current_user: dict = Depends(get_current_user)) -> List[Topic]:
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


@router.get("/{user_uid}/with-review-status")
async def get_topics_with_review_status(
    user_uid: str, current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get all topics for a user with FSRS review status"""
    # Verify user can access these topics
    if current_user.get("uid") != user_uid:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        topic_service = TopicService()
        fsrs_service = FSRSService()

        # Get all user topics
        topics = await topic_service.get_user_topics(user_uid)

        # Enhance each topic with review status
        topics_with_status = []
        current_time = datetime.now()

        for topic in topics:
            # Calculate review status
            is_due = False
            is_overdue = False
            days_until_review = None
            review_urgency = "not_scheduled"

            if topic.nextReviewAt:
                time_diff = topic.nextReviewAt - current_time
                days_until_review = time_diff.days

                if time_diff.total_seconds() <= 0:
                    is_overdue = True
                    review_urgency = "overdue"
                elif days_until_review <= 1:
                    is_due = True
                    review_urgency = "due_today"
                elif days_until_review <= 3:
                    review_urgency = "due_soon"
                else:
                    review_urgency = "scheduled"

            # Calculate retention if last reviewed
            retention_probability = None
            if topic.lastReviewedAt:
                days_since_review = (current_time - topic.lastReviewedAt).days
                retention_probability = fsrs_service.calculate_retention_probability(
                    topic.fsrsParams, days_since_review
                )

            topic_data = {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
                "questionCount": len(topic.questionBank),
                "createdAt": topic.createdAt,
                "lastReviewedAt": topic.lastReviewedAt,
                "nextReviewAt": topic.nextReviewAt,
                "isDue": is_due,
                "isOverdue": is_overdue,
                "daysUntilReview": days_until_review,
                "reviewUrgency": review_urgency,
                "retentionProbability": retention_probability,
                "fsrsParams": {
                    "ease": topic.fsrsParams.ease,
                    "interval": topic.fsrsParams.interval,
                    "repetition": topic.fsrsParams.repetition,
                },
            }

            topics_with_status.append(topic_data)

        # Sort by review urgency (overdue first, then due today, etc.)
        urgency_order = {
            "overdue": 0,
            "due_today": 1,
            "due_soon": 2,
            "scheduled": 3,
            "not_scheduled": 4,
        }
        topics_with_status.sort(key=lambda x: urgency_order.get(x["reviewUrgency"], 5))

        return topics_with_status

    except Exception as e:
        logger.error("Error getting topics with review status", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to get topics with review status: {safe_error_message}")


@router.get("/{user_uid}/due-today")
async def get_todays_reviews(user_uid: str, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get topics due for review today"""
    # Verify user can access these topics
    if current_user.get("uid") != user_uid:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        topic_service = TopicService()

        # Get all user topics
        topics = await topic_service.get_user_topics(user_uid)

        current_time = datetime.now()
        end_of_today = current_time.replace(hour=23, minute=59, second=59)

        due_topics = []
        overdue_topics = []
        upcoming_topics = []

        for topic in topics:
            if not topic.nextReviewAt:
                continue

            if topic.nextReviewAt <= current_time:
                # Overdue
                days_overdue = (current_time - topic.nextReviewAt).days
                topic_data = {
                    "id": topic.id,
                    "name": topic.name,
                    "description": topic.description,
                    "questionCount": len(topic.questionBank),
                    "nextReviewAt": topic.nextReviewAt,
                    "daysOverdue": days_overdue,
                    "fsrsParams": topic.fsrsParams.dict(),
                }
                overdue_topics.append(topic_data)

            elif topic.nextReviewAt <= end_of_today:
                # Due today
                topic_data = {
                    "id": topic.id,
                    "name": topic.name,
                    "description": topic.description,
                    "questionCount": len(topic.questionBank),
                    "nextReviewAt": topic.nextReviewAt,
                    "fsrsParams": topic.fsrsParams.dict(),
                }
                due_topics.append(topic_data)

            elif topic.nextReviewAt <= current_time + timedelta(days=3):
                # Due within 3 days
                days_until = (topic.nextReviewAt - current_time).days
                topic_data = {
                    "id": topic.id,
                    "name": topic.name,
                    "description": topic.description,
                    "questionCount": len(topic.questionBank),
                    "nextReviewAt": topic.nextReviewAt,
                    "daysUntil": days_until,
                    "fsrsParams": topic.fsrsParams.dict(),
                }
                upcoming_topics.append(topic_data)

        # Sort by urgency
        overdue_topics.sort(key=lambda x: x["daysOverdue"], reverse=True)  # Most overdue first
        due_topics.sort(key=lambda x: x["nextReviewAt"])  # Earliest first
        upcoming_topics.sort(key=lambda x: x["nextReviewAt"])  # Earliest first

        return {
            "overdue": overdue_topics,
            "dueToday": due_topics,
            "upcoming": upcoming_topics,
            "totalDue": len(overdue_topics) + len(due_topics),
            "totalOverdue": len(overdue_topics),
            "reviewDate": current_time.isoformat(),
        }

    except Exception as e:
        logger.error("Error getting today's reviews", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to get today's reviews: {safe_error_message}")


@router.get("/{user_uid}/review-statistics")
async def get_review_statistics(user_uid: str, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get review statistics and insights for a user"""
    # Verify user can access this data
    if current_user.get("uid") != user_uid:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        topic_service = TopicService()
        fsrs_service = FSRSService()

        # Get all user topics
        topics = await topic_service.get_user_topics(user_uid)

        if not topics:
            return {
                "totalTopics": 0,
                "studyStreak": 0,
                "averageRetention": 0,
                "weeklyLoad": 0,
                "insights": [],
            }

        current_time = datetime.now()

        # Calculate statistics
        total_topics = len(topics)
        topics_with_reviews = [t for t in topics if t.lastReviewedAt]

        # Calculate average retention
        total_retention = 0
        retention_count = 0

        # Weekly review load (next 7 days)
        weekly_reviews = 0
        next_week = current_time + timedelta(days=7)

        for topic in topics:
            # Retention calculation
            if topic.lastReviewedAt:
                days_since = (current_time - topic.lastReviewedAt).days
                retention = fsrs_service.calculate_retention_probability(topic.fsrsParams, days_since)
                total_retention += retention
                retention_count += 1

            # Weekly load calculation
            if topic.nextReviewAt and current_time <= topic.nextReviewAt <= next_week:
                weekly_reviews += 1

        average_retention = (total_retention / retention_count) if retention_count > 0 else 0

        # Calculate study streak (consecutive days with reviews)
        study_streak = await calculate_study_streak(topics_with_reviews)

        # Generate high-level insights based on review status
        insights = []
        if topics_with_reviews:
            overdue_topics = len([t for t in topics_with_reviews if t.get("isOverdue")])
            due_today_topics = len([t for t in topics_with_reviews if t.get("isDue")])
            if overdue_topics > 0:
                insights.append(f"{overdue_topics} topics are overdue for review")
            if due_today_topics > 0:
                insights.append(f"{due_today_topics} topics are due for review today")
        else:
            overdue_topics = 0

        if len(topics_with_reviews) < total_topics * 0.5:
            insights.append("Many topics haven't been reviewed yet - consider starting some study sessions")

        return {
            "totalTopics": total_topics,
            "reviewedTopics": len(topics_with_reviews),
            "studyStreak": study_streak,
            "averageRetention": round(average_retention, 2),
            "weeklyLoad": weekly_reviews,
            "overdueCount": overdue_topics,
            "insights": insights,
            "lastUpdated": current_time.isoformat(),
        }

    except Exception as e:
        logger.error("Error getting review statistics", extra={"error_detail": str(e)})
        safe_error_message = str(e).replace("{", "{{").replace("}", "}}")
        raise HTTPException(500, f"Failed to get review statistics: {safe_error_message}")


async def calculate_study_streak(topics_with_reviews: List[Topic]) -> int:
    """Calculate consecutive study streak in days"""
    if not topics_with_reviews:
        return 0

    # Get all unique review dates
    review_dates = set()
    for topic in topics_with_reviews:
        if topic.lastReviewedAt:
            review_date = topic.lastReviewedAt.date()
            review_dates.add(review_date)

    if not review_dates:
        return 0

    # Sort dates in descending order
    sorted_dates = sorted(review_dates, reverse=True)

    # Calculate streak starting from most recent date
    current_date = datetime.now().date()
    streak = 0

    for i, review_date in enumerate(sorted_dates):
        expected_date = current_date - timedelta(days=i)

        if review_date == expected_date:
            streak += 1
        else:
            break

    return streak
