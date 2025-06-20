from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


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
    createdAt: Optional[datetime] = None
    nextReviewAt: Optional[datetime] = None 