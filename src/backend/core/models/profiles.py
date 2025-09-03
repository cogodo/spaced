from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ModelProfile:
    """Immutable model profile for OpenAI chat completions.

    Notes:
    - GPT‑5 uses max_completion_tokens (not max_tokens)
    - Temperature is not supported for GPT‑5 and should not be sent
    """

    name: str
    model: str
    max_completion_tokens: int
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None

    def apply(self, **overrides: Any) -> Dict[str, Any]:
        """Return request params dict for OpenAI create(), with optional overrides.

        Temperature is intentionally omitted for GPT‑5 compatibility.
        """
        params: Dict[str, Any] = {
            "model": self.model,
            "max_completion_tokens": self.max_completion_tokens,
        }
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty

        # Allow safe overrides (e.g., model, max_completion_tokens)
        for key, value in overrides.items():
            if value is not None:
                params[key] = value
        return params


# Core profiles for common use cases
GENERATION_SINGLE = ModelProfile(
    name="generation_single",
    model="gpt-5",
    max_completion_tokens=500,
)

GENERATION_BULK = ModelProfile(
    name="generation_bulk",
    model="gpt-5",
    max_completion_tokens=1500,
)

REFINEMENT_BULK = ModelProfile(
    name="refinement_bulk",
    model="gpt-5",
    max_completion_tokens=1800,
)

ANALYSIS = ModelProfile(
    name="analysis",
    model="gpt-5",
    max_completion_tokens=500,
)

CONVERSATION_SUMMARY = ModelProfile(
    name="conversation_summary",
    model="gpt-5",
    max_completion_tokens=500,
)

CONVERSATION_STEP = ModelProfile(
    name="conversation_step",
    model="gpt-5",
    max_completion_tokens=2048,
)

ROUTING = ModelProfile(
    name="routing",
    model="gpt-5",
    max_completion_tokens=256,
)

SCORING = ModelProfile(
    name="scoring",
    model="gpt-5",
    max_completion_tokens=600,
)

FEEDBACK = ModelProfile(
    name="feedback",
    model="gpt-5",
    max_completion_tokens=600,
)

CLARIFICATION = ModelProfile(
    name="clarification",
    model="gpt-5",
    max_completion_tokens=600,
)
