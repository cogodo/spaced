from typing import Any, Dict, List, Literal

from pydantic import BaseModel


class Question(BaseModel):
    id: str
    topicId: str
    text: str
    type: Literal["multiple_choice", "short_answer", "explanation"]
    difficulty: int
    metadata: Dict[str, Any] = {}


class CreateQuestionRequest(BaseModel):
    text: str
    type: Literal["multiple_choice", "short_answer", "explanation"]
    difficulty: int = 1


class UpdateQuestionRequest(BaseModel):
    text: str
    type: Literal["multiple_choice", "short_answer", "explanation"]
    difficulty: int


class CreateQuestionsRequest(BaseModel):
    questions: List[CreateQuestionRequest]
