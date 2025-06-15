from typing import TypedDict, List, Dict, Optional, Any

class MessagesState(MessagesState):
    pass

class GraphState(TypedDict):
    """
    Phase 4 State Schema - Clean, focused state management for LangGraph
    """
    # session_id: str = ""
    # user_id: Optional[str] = None
    
    topics: List[str] = []
    current_topic_index: int = 0
    topic_scores: Dict[str, int] = {}
    topic_evaluations: Dict[str, str] = {}
    
    question_list: List[str]
    current_question_idx: int
    topic_question_summaries: List[Dict[str, Any]] = []

    max_topics: int = 2
    max_questions_per_topic: int = 2