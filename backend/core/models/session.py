from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class Response(BaseModel):
    questionId: str
    answer: str
    score: int  # 0-5 grading
    timestamp: datetime


class Session(BaseModel):
    id: str
    userUid: str
    topicId: str
    questionIndex: int = 0
    questionIds: List[str] = []
    responses: List[Response] = []
    startedAt: datetime
    nextReviewAt: Optional[datetime] = None
    
    @classmethod
    def model_validate_dict(cls, data: dict):
        """Helper method for loading from Firestore with nested objects"""
        if 'responses' in data:
            # Convert response dicts back to Response objects
            data['responses'] = [Response(**r) if isinstance(r, dict) else r for r in data['responses']]
        return cls(**data) 