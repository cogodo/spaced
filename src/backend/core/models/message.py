from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    text: str = Field(..., description="Message text")
    isUser: bool = Field(..., description="True if message is from user")
    isSystem: bool = Field(False, description="True if message is a system message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    messageIndex: Optional[int] = Field(None, description="Index of the message in the session")
    isVoice: Optional[bool] = Field(False, description="True if message is from voice input")
