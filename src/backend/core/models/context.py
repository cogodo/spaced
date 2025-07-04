from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TurnState(str, Enum):
    # The system is waiting for the user's initial answer to a question
    AWAITING_INITIAL_ANSWER = "AWAITING_INITIAL_ANSWER"
    # The system is waiting for the user's response to feedback/hint
    AWAITING_FOLLOW_UP = "AWAITING_FOLLOW_UP"
    # The system has evaluated the user and is asking them what to do next
    AWAITING_NEXT_ACTION = "AWAITING_NEXT_ACTION"


class Message(BaseModel):
    """Message in session subcollection - embeds question text for efficiency"""

    id: str
    questionId: str
    questionText: str  # Embedded to avoid extra reads
    answerText: str
    score: int  # 0-5 grading
    timestamp: datetime


class Context(BaseModel):
    chatId: str = Field(..., description="Unique identifier for the chat session")
    userUid: str = Field(..., description="User ID of the owner")
    topicId: str = Field(..., description="The topic being discussed")
    questionIds: List[str] = Field(default_factory=list, description="List of question IDs for the session")
    questionIdx: int = Field(0, description="Index of the current question")
    scores: Dict[str, int] = Field(default_factory=dict, description="Scores for each question")
    startedAt: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    endedAt: Optional[datetime] = Field(None, description="Session end time")
    updatedAt: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    turnState: TurnState = Field(
        TurnState.AWAITING_INITIAL_ANSWER, description="The current state of the question-answer turn."
    )
    initialScore: Optional[int] = Field(None, description="The score of the user's first attempt.")

    def end_session(self):
        self.endedAt = datetime.utcnow()

    def touch(self):
        self.updatedAt = datetime.utcnow()

    class Config:
        """Pydantic configuration."""

        # This allows the model to be created from ORM objects
        orm_mode = True

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
