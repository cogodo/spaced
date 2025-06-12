from typing import TypedDict, List, Dict, Optional, Any
from my_agent.utils.firebase_service import Task

class GraphState(TypedDict):
    # Session type: "due_items" or "custom_topics"
    session_type: str
    
    # User authentication
    user_id: Optional[str]
    
    # For custom_topics: user-provided topics
    # For due_items: task names from Firebase
    topics: List[str]
    
    # For due_items sessions: full task objects with FSRS data
    tasks: Optional[List[Any]]

    # Index of the current topic/task (0-based)
    current_topic_index: int

    # How many questions have been asked so far for the current topic
    question_count: int

    # A running list of {"question": str, "answer": str, "topic": str} pairs
    history: List[Dict[str, Any]]

    # The most recent user input (or None when it's time to ask the first question)
    user_input: Optional[str]

    # The next question to send back to the user (filled by the respond node)
    next_question: Optional[str]

    # Whether we've exhausted all topics/questions and should evaluate
    done: bool

    # Once done=True, the evaluator will fill this mapping: topic -> FSRS score (0–5)
    scores: Optional[Dict[str, int]]

    # Configuration: maximum number of topics to cover (e.g. 3)
    max_topics: int

    # Configuration: maximum questions per topic (e.g. 7)
    max_questions: int

    # For due_items: count of total due tasks available
    due_tasks_count: Optional[int]

    # Current task being reviewed (for due_items sessions)
    current_task: Optional[str]

    # Progress tracking for UI
    progress: Optional[str]

    # Track question types and contexts
    question_types: List[Dict[str, Any]]

    # Phase 5: Advanced Features
    
    # Adaptive session management
    adaptive_session_length: Optional[bool]
    performance_threshold: Optional[float]  # For early completion if performing well
    struggle_threshold: Optional[float]     # For extended session if struggling
    
    # Multi-task connections and analytics
    topic_connections: Optional[Dict[str, List[str]]]  # topic -> related topics
    cross_topic_insights: Optional[List[Dict[str, Any]]]  # Connections found during session
    
    # Session analytics and summaries
    session_start_time: Optional[str]
    session_end_time: Optional[str]
    performance_trends: Optional[Dict[str, List[float]]]  # topic -> score progression
    learning_momentum: Optional[float]  # Overall session momentum score
    
    # Advanced question generation
    question_difficulty_progression: Optional[List[float]]  # Track difficulty changes
    answer_confidence_scores: Optional[List[float]]  # Confidence in each answer
    personalized_question_bank: Optional[Dict[str, List[str]]]  # User-specific questions
    
    # Intelligent session adaptation
    session_completion_reason: Optional[str]  # "max_questions", "performance_achieved", "time_limit", etc.
    recommended_next_session: Optional[Dict[str, Any]]  # Smart recommendations for next study session
    
    # Enhanced evaluation metrics
    detailed_performance_analysis: Optional[Dict[str, Any]]  # Deep performance insights
    learning_velocity: Optional[float]  # Rate of improvement during session
    retention_prediction: Optional[Dict[str, float]]  # Predicted retention for each topic
