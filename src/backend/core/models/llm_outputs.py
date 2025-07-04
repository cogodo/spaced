from enum import Enum

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


class RoutingDecision(BaseModel):
    """The routing decision for the user's response."""

    next_action: NextAction = Field(..., description="The determined next action based on user input.")
