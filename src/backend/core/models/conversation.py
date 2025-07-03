from typing import List, Optional

from pydantic import BaseModel, Field

from .question import Question


class Turn(BaseModel):
    """
    Represents a single turn in a conversation, with user input and bot response.
    """

    user_input: str
    bot_response: str


# --- State Management Models ---


class ConversationState(BaseModel):
    """
    Represents the user's state in a conversation, stored in Redis.
    """

    user_id: str
    topic_id: str
    question_index: int = 0
    score_history: List[int] = Field(default_factory=list, exclude=True)
    hints_given: int = 0
    misconceptions: List[str] = Field(default_factory=list, exclude=True)
    question_ids: List[str] = Field(default_factory=list)
    answered_question_ids: List[str] = Field(default_factory=list)
    history: List[Turn] = Field(default_factory=list, exclude=True)
    turn_count: int = 0
    questions: List[Question] = Field(default_factory=list, exclude=True)


# --- LLM Interaction Models ---


class LLMStateUpdate(BaseModel):
    """
    Defines the structure for state updates returned by the LLM.
    """

    score: int = Field(description="Score from 0 to 5 for the user's last answer.")
    hint_given: bool = Field(default=False, description="True if a hint was provided.")
    misconception: Optional[str] = Field(default=None, description="A summary of any misconception identified.")


class LLMResponse(BaseModel):
    """
    Defines the expected JSON structure from the LLM.
    """

    user_facing_response: str = Field(description="The conversational response to show to the user.")
    state_update: LLMStateUpdate
