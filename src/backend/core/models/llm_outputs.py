from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FSRSScore(BaseModel):
    """The FSRS score for a user's answer."""

    score: int = Field(..., description="The score from 1-5, based on FSRS definitions.", ge=1, le=5)
    reasoning: str = Field(..., description="A brief justification for the assigned score.")


class ClarificationImpact(BaseModel):
    """The impact analysis of a clarification response."""

    adjusted_score: int = Field(
        ...,
        description="The new score for the original question after providing clarification (1 or 3).",
        ge=1,
        le=3,
    )
    reasoning: str = Field(..., description="Justification for why the clarification leads to this adjusted score.")


class NextAction(str, Enum):
    """The next action to take in the conversation."""

    MOVE_TO_NEXT_QUESTION = "next_question"
    AWAIT_CLARIFICATION = "clarification"
    END_CHAT = "end_chat"


class CombinedStateUpdate(BaseModel):
    """Validated state update returned by CombinedService."""

    score: int = Field(..., ge=1, le=5, description="The final score (1..5)")
    reasoning: str = Field(..., max_length=200, description="Brief justification, <=200 chars")
    hint_given: bool = Field(..., description="True if a hint or leading question was given")
    misconception: Optional[str] = Field(None, description="Brief misconception summary or null")
    next_action: NextAction = Field(..., description="Next action classification")


class CombinedTurnPayload(BaseModel):
    """Validated payload returned by CombinedService."""

    user_facing_response: str = Field(..., max_length=800)
    state_update: CombinedStateUpdate


class RoutingDecision(BaseModel):
    """The routing decision for the user's response."""

    next_action: NextAction = Field(..., description="The determined next action based on user input.")
