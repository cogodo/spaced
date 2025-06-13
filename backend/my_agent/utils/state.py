from typing import TypedDict, List, Dict, Optional, Any
from my_agent.utils.firebase_service import Task

class GraphState(TypedDict):
    # Core session data
    session_type: str  # "due_items" or "custom_topics"
    user_id: Optional[str]
    
    # Topic management - NEW: Explicit topic source tracking
    topics: List[str]  # All topics for this session
    topic_sources: Dict[str, Dict]  # Source metadata for each topic
    current_topic_index: int
    completed_topics: List[str]
    
    # Topic-by-topic scoring - NEW: Individual topic evaluation
    topic_scores: Dict[str, int]  # topic -> score (0-5)
    topic_evaluations: Dict[str, Dict]  # topic -> full evaluation details
    
    # Conversation management - SIMPLIFIED: Remove legacy fields
    user_input: Optional[str]
    next_question: Optional[str]
    conversation_history: List[Dict[str, Any]]  # NEW: Cleaner conversation tracking
    message_count: int
    
    # Session completion - SIMPLIFIED: Remove complex analytics
    session_complete: bool
    session_summary: Optional[Dict[str, Any]]
    
    # PHASE 2: Question-Based Conversation Fields
    current_question: Optional[Dict[str, Any]]  # Current active question with conversation history
    current_topic_id: Optional[str]  # Firebase-safe topic ID
    topic_question_summaries: List[Dict[str, Any]]  # Question summaries for current topic
    session_settings: Optional[Dict[str, Any]]  # User preferences (max_questions_per_topic, etc.)
    
    # Firebase integration (for due_items sessions)
    due_tasks: Optional[List[Any]]  # Original task objects from Firebase
    custom_topics: Optional[List[str]]  # For custom_topics sessions
    
    # Configuration
    max_messages: int  # Hard limit (40)
    
    # Legacy fields - DEPRECATED: Keep for backward compatibility during transition
    # TODO: Remove these after full migration
    tasks: Optional[List[Any]]
    question_count: Optional[int]
    history: Optional[List[Dict[str, Any]]]
    done: Optional[bool]
    scores: Optional[Dict[str, int]]
    max_topics: Optional[int]
    max_questions: Optional[int]
    due_tasks_count: Optional[int]
    current_task: Optional[str]
    progress: Optional[str]
    question_types: Optional[List[Dict[str, Any]]]
    
    # Legacy Phase 5 fields - DEPRECATED
    adaptive_session_length: Optional[bool]
    performance_threshold: Optional[float]
    struggle_threshold: Optional[float]
    topic_connections: Optional[Dict[str, List[str]]]
    cross_topic_insights: Optional[List[Dict[str, Any]]]
    session_start_time: Optional[str]
    session_end_time: Optional[str]
    performance_trends: Optional[Dict[str, List[float]]]
    learning_momentum: Optional[float]
    question_difficulty_progression: Optional[List[float]]
    answer_confidence_scores: Optional[List[float]]
    personalized_question_bank: Optional[Dict[str, List[str]]]
    session_completion_reason: Optional[str]
    recommended_next_session: Optional[Dict[str, Any]]
    detailed_performance_analysis: Optional[Dict[str, Any]]
    learning_velocity: Optional[float]
    retention_prediction: Optional[Dict[str, float]]
    
    # PHASE 4: Real-Time Adaptive Intelligence Fields  
    live_performance_metrics: Optional[Dict[str, float]]  # understanding, confidence, engagement
    adaptive_difficulty_level: Optional[float]  # 0.0-1.0, adjusts in real-time
    learned_user_preferences: Optional[Dict[str, Any]]  # discovered during conversation
    question_adaptation_history: Optional[List[Dict]]  # track how questions were adapted
    
    # Real-time personalization
    detected_learning_style: Optional[str]  # visual, verbal, experiential, kinesthetic
    cognitive_load_level: Optional[str]  # low, medium, high, overloaded
    engagement_trend: Optional[str]  # increasing, stable, declining
    understanding_velocity: Optional[float]  # how quickly they're grasping concepts
    
    # Intelligent conversation management
    conversation_intelligence: Optional[Dict[str, Any]]  # teaching strategy, depth level, etc.
    adaptive_conversation_history: Optional[List[Dict]]  # enhanced conversation tracking
    personalization_insights: Optional[Dict[str, Any]]  # discovered preferences and patterns
    
    # Advanced session optimization
    optimal_question_sequence: Optional[List[str]]  # dynamically reordered questions
    learning_momentum_score: Optional[float]  # 0.0-1.0 momentum tracking
    session_optimization_log: Optional[List[Dict]]  # track all adaptations made
