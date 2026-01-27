from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProfile:
    """Token budget configuration for LLM operations."""

    name: str
    max_completion_tokens: int


# Token budgets for different operation types
GENERATION_SINGLE = ModelProfile(
    name="generation_single",
    max_completion_tokens=500,
)

GENERATION_BULK = ModelProfile(
    name="generation_bulk",
    max_completion_tokens=1500,
)

REFINEMENT_BULK = ModelProfile(
    name="refinement_bulk",
    max_completion_tokens=1800,
)

ANALYSIS = ModelProfile(
    name="analysis",
    max_completion_tokens=500,
)

CONVERSATION_SUMMARY = ModelProfile(
    name="conversation_summary",
    max_completion_tokens=500,
)

CONVERSATION_STEP = ModelProfile(
    name="conversation_step",
    max_completion_tokens=2048,
)

ROUTING = ModelProfile(
    name="routing",
    max_completion_tokens=256,
)

SCORING = ModelProfile(
    name="scoring",
    max_completion_tokens=600,
)

FEEDBACK = ModelProfile(
    name="feedback",
    max_completion_tokens=600,
)

CLARIFICATION = ModelProfile(
    name="clarification",
    max_completion_tokens=600,
)
