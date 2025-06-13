from typing import TypedDict, List, Dict, Optional, Any
from my_agent.utils.firebase_service import Task
from datetime import datetime

class GraphState(TypedDict):
    """
    Phase 4 State Schema - Clean, focused state management
    """
    
    # Session Management
    session_id: str
    session_type: str  # "due_items" or "custom_topics"
    user_id: Optional[str]
    message_count: int
    max_messages: int
    session_complete: bool
    session_summary: Optional[Dict[str, Any]]
    
    # Topic Management
    topics: List[str]
    current_topic_index: int
    completed_topics: List[str]
    topic_scores: Dict[str, int]
    topic_evaluations: Dict[str, Any]
    topic_sources: Dict[str, Dict[str, Any]]
    
    # Question-Based Learning (Phase 4)
    current_question: Optional[Dict[str, Any]]
    current_topic_id: Optional[str]
    topic_question_summaries: List[Dict[str, Any]]
    session_settings: Dict[str, Any]
    
    # Conversation Management
    conversation_history: List[Dict[str, Any]]
    user_input: Optional[str]
    next_question: Optional[str]
    
    # Session Data
    due_tasks: Optional[List[Any]]
    custom_topics: Optional[List[str]]
    max_topics: int
    max_questions: int
