from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    """Message in session subcollection - embeds question text for efficiency"""

    id: str
    questionId: str
    questionText: str  # Embedded to avoid extra reads
    answerText: str
    score: int  # 0-5 grading
    timestamp: datetime


class Session(BaseModel):
    """Session metadata - messages stored in subcollection"""

    id: str
    userUid: str
    topicId: str
    questionIndex: int = 0
    questionIds: List[str] = []
    startedAt: datetime
    nextReviewAt: Optional[datetime] = None
    # Track which questions have been answered across multiple sessions
    answeredQuestionIds: List[str] = []
    # Track current session progress (resets each session, max 5)
    currentSessionQuestionCount: int = 0
    maxQuestionsPerSession: int = 5
    # Backward compatibility field (will be ignored in new sessions)
    responses: List = []

    @classmethod
    def model_validate_dict(cls, data: dict, doc_id: str = None, user_uid: str = None):
        """Helper method for loading from Firestore with required field handling"""
        # Remove old responses field if present (migration compatibility)
        if "responses" in data:
            del data["responses"]

        # Ensure required fields are present (populate from document context if missing)
        if "id" not in data and doc_id:
            data["id"] = doc_id
        if "userUid" not in data and user_uid:
            data["userUid"] = user_uid

        # Ensure backward compatibility with old sessions missing new fields
        if "answeredQuestionIds" not in data:
            data["answeredQuestionIds"] = []
        if "currentSessionQuestionCount" not in data:
            data["currentSessionQuestionCount"] = 0
        if "maxQuestionsPerSession" not in data:
            data["maxQuestionsPerSession"] = 5

        return cls(**data)
