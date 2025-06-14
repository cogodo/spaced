from typing import TypedDict, List, Dict, Optional, Any
from datetime import datetime

class GraphState(TypedDict):
    """
    Phase 4 State Schema - Clean, focused state management for LangGraph
    """
    
    # Standard Chat Interface
    messages: List[Dict[str, Any]] = []
    
    # Session Management
    session_id: str = ""
    session_type: str = "custom_topics"  # "due_items" or "custom_topics"
    user_id: Optional[str] = None
    message_count: int = 0
    max_messages: int = 50
    session_complete: bool = False
    session_summary: Optional[Dict[str, Any]] = None
    
    # Topic Management
    topics: List[str] = []
    current_topic_index: int = 0
    completed_topics: List[str] = []
    topic_scores: Dict[str, int] = {}
    topic_evaluations: Dict[str, Any] = {}
    topic_sources: Dict[str, Dict[str, Any]] = {}
    
    # Question-Based Learning (Phase 4)
    current_question: Optional[Dict[str, Any]] = None
    current_topic_id: Optional[str] = None
    topic_question_summaries: List[Dict[str, Any]] = []
    session_settings: Dict[str, Any] = {}
    
    # Conversation Management
    conversation_history: List[Dict[str, Any]] = []
    user_input: Optional[str] = None
    next_question: Optional[str] = None
    
    # Session Data
    due_tasks: Optional[List[Any]] = None
    custom_topics: Optional[List[str]] = None
    max_topics: int = 5
    max_questions: int = 10 