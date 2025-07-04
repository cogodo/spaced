# Chat Flow Implementation Plan (v3)

This document outlines the plan to implement a new, dynamic, and LLM-driven conversational learning flow. This plan has been updated to incorporate detailed feedback on scoring, LLM usage, and handling user clarifications.

## 1. Implementation Strategy: A Two-Phase Approach

To manage complexity, we will implement the new chat flow in two distinct phases:

### Phase 1: Architectural Skeleton (Current Focus)
The primary goal of this phase is to build the complete, end-to-end structure of the application without making any actual LLM calls.
- **Function Stubs**: All new services and methods will be created as "stubs" — empty functions with detailed comments and type hints that describe their purpose, inputs, and outputs.
- **Mocked LLM Calls**: Any function that is intended to call an LLM will instead have a `// TODO: LLM call` comment and will return a hardcoded, "dummy" response. This dummy data will conform to the required Pydantic schema, allowing the rest of the system to function as if a real LLM call were made.

### Phase 2: LLM Integration
Once the architectural skeleton is in place and verified, we will proceed with implementing the core intelligence.
- **Real Logic**: The placeholder comments and dummy data will be replaced with actual client calls to the OpenAI API.
- **Prompt Engineering**: We will focus on crafting the specific prompts required to achieve the desired behavior from the models.

## 2. Core Concepts & Architecture

The new architecture will be orchestrated by a central `ConversationService`. Each interaction from the user will be handled by a single API endpoint, which will delegate to the `ConversationService` to manage the state and execute the appropriate logic for that turn.

State will be managed in the `Context` object, which will be extended to track the user's progress *within* a single question, not just through the list of questions.

We will leverage Pydantic for structured outputs from an **OpenAI GPT-4 class model** to create a reliable, state-driven system.

## 3. `Context` Model Extension

The existing `Context` model in `src/backend/core/models/context.py` needs to be updated to track the state of a single question-answer-feedback loop.

```python
# src/backend/core/models/context.py
from enum import Enum

class TurnState(str, Enum):
    # The system is waiting for the user's initial answer to a question
    AWAITING_INITIAL_ANSWER = "AWAITING_INITIAL_ANSWER"
    # The system is waiting for the user's response to feedback/hint
    AWAITING_FOLLOW_UP = "AWAITING_FOLLOW_UP"
    # The system has evaluated the user and is asking them what to do next
    AWAITING_NEXT_ACTION = "AWAITING_NEXT_ACTION"

class Context(BaseModel):
    # ... existing fields ...
    turnState: TurnState = Field(TurnState.AWAITING_INITIAL_ANSWER, description="The current state of the question-answer turn.")
    initialScore: Optional[int] = Field(None, description="The score of the user's first attempt.")
```

## 4. Pydantic Models for Structured LLM Outputs

We will create a new file, `src/backend/core/models/llm_outputs.py`, to house the Pydantic models for structured LLM outputs.

```python
# src/backend/core/models/llm_outputs.py
from pydantic import BaseModel, Field
from enum import Enum

class FSRSScore(BaseModel):
    """The FSRS score for a user's answer."""
    score: int = Field(..., description="The score from 1-5, based on FSRS definitions.", ge=1, le=5)
    reasoning: str = Field(..., description="A brief justification for the assigned score.")

class ClarificationImpact(BaseModel):
    """The impact analysis of a clarification response."""
    adjusted_score: int = Field(..., description="The new score for the original question after providing clarification (1 or 3).", ge=1, le=3)
    reasoning: str = Field(..., description="Justification for why the clarification leads to this adjusted score.")

class NextAction(str, Enum):
    """The next action to take in the conversation."""
    MOVE_TO_NEXT_QUESTION = "next_question"
    AWAIT_CLARIFICATION = "clarification"
    END_CHAT = "end_chat"

class RoutingDecision(BaseModel):
    """The routing decision for the user's response."""
    next_action: NextAction = Field(..., description="The determined next action based on user input.")
```

## 5. New and Updated Services

### a. `EvaluationService` (New)
- **File**: `src/backend/core/services/evaluation_service.py`
- **Purpose**: To interact with an LLM to score a user's answer based on conversational FSRS definitions.
- **Methods**:
    - `async def score_answer(question: Question, answer: str, after_hint: bool) -> FSRSScore`: The prompt for this service will be context-aware. If `after_hint` is true, the scoring will be more lenient (e.g., a correct answer might map to a score of 3 or 4, not 5). The scoring definitions will be:
        - **5 (Excellent)**: A really good, comprehensive answer. Doesn't have to be literary perfection.
        - **4 (Good)**: A correct answer that might be the result of a gentle prod or hint.
        - **3 (Okay)**: Correct, but with minor errors, or correct after a significant hint.
        - **2 (Incorrect, but shows some recall)**: User remembers some concepts but applies them wrongly.
        - **1 (Incorrect)**: Completely wrong or irrelevant answer.

### b. `FeedbackService` (New)
- **File**: `src/backend/core/services/feedback_service.py`
- **Purpose**: To generate helpful, context-aware feedback for the user.
- **Methods**:
    - `async def generate_feedback(question: Question, answer: str, score: FSRSScore) -> str`: Takes the context and generates a tailored response. If the score is high, it's a simple acknowledgment. If low, it's a hint to guide the user.

### c. `RoutingService` (New)
- **File**: `src/backend/core/services/routing_service.py`
- **Purpose**: To determine the user's intent after they've received feedback or asked a question.
- **Methods**:
    - `async def determine_next_action(user_response: str) -> RoutingDecision`: Classifies user intent into a `NextAction`.

### d. `ClarificationService` (New)
- **File**: `src/backend/core/services/clarification_service.py`
- **Purpose**: To handle the specific flow where a user asks a clarifying question.
- **Methods**:
    - `async def handle_clarification(original_question: Question, user_clarification_request: str) -> Tuple[str, ClarificationImpact]`:
        1.  Calls an LLM to generate a direct, informative answer to the `user_clarification_request`.
        2.  Makes a *second* LLM call to perform an impact analysis: "Given the original question and the answer I just provided for the user's side-question, how much does this help? If it essentially gives away the answer, the adjusted score is 1. If it's only adjacently helpful, the score is 3."
        3.  Returns both the informative answer and the `ClarificationImpact` object.

### e. `ConversationService` (New - The Orchestrator)
- **File**: `src/backend/core/services/conversation_service.py`
- **Purpose**: The main service to manage the lifecycle of a single conversational turn.
- **Methods**:
    - `async def process_turn(chat_id: str, user_uid: str, user_input: str) -> str`: The primary method that orchestrates the entire flow, calling the other services based on the `Context.turnState`.

## 6. Step-by-Step Implementation Plan

### Phase 1: Architectural Skeleton

1.  **Step 1: Foundational Models (Complete)**:
    -   Update `context.py` with the new `TurnState` enum and fields.
    -   Create `src/backend/core/models/llm_outputs.py` with the `FSRSScore`, `ClarificationImpact`, and `RoutingDecision` models.
2.  **Step 2: Stub Core Logic Services**:
    -   Create the files and method stubs for `EvaluationService`, `FeedbackService`, `RoutingService`, and `ClarificationService`. Each method will contain a detailed docstring and return mocked Pydantic objects.
3.  **Step 3: Stub the Orchestrator**:
    -   Implement the `ConversationService` with its primary `process_turn` method. The internal logic will call the stubbed services and correctly route based on the mocked data.
4.  **Step 4: API Exposure**:
    -   Create the `POST /api/v1/chat/{chat_id}/turn` endpoint in `chat.py`.
    -   Connect the endpoint to the `ConversationService`.
5.  **Step 5: Integration Testing**:
    -   Test the full, end-to-end flow with the mocked data to ensure the state machine and data pathways are working as expected.

### Phase 2: LLM Integration
*(To be executed after Phase 1 is complete and approved)*

1.  **Step 6: Implement LLM Services**:
    -   Fill in the logic for the `EvaluationService`, `FeedbackService`, `RoutingService`, and `ClarificationService`, replacing dummy data with real OpenAI API calls.
2.  **Step 7: Final Testing**:
    -   Conduct thorough end-to-end testing with live LLM responses to refine prompts and verify the behavior of the complete system.

This structured approach ensures we build the system from the ground up, starting with data models and moving to services and finally the API, which should make the process manageable and robust. 