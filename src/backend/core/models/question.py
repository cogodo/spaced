from typing import Dict, Any, Literal
from pydantic import BaseModel


class Question(BaseModel):
    id: str
    topicId: str
    text: str
    type: Literal["multiple_choice", "short_answer", "explanation"]
    difficulty: int
    metadata: Dict[str, Any] = {}
