from typing import List, Dict, Any
from pydantic import BaseModel


class FSRSParams(BaseModel):
    ease: float = 2.5
    interval: int = 1
    repetition: int = 0


class Topic(BaseModel):
    id: str
    ownerUid: str
    name: str
    description: str
    questionBank: List[str] = []
    fsrsParams: FSRSParams = FSRSParams()
    regenerating: bool = False 