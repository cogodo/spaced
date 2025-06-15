import random
from typing import Dict, List, Tuple, Any
import re
from datetime import datetime, timezone
import os
import openai
import json
from dotenv import load_dotenv
from agent.state import GraphState
from agent.utils.firebase_service import firebase_service

# Load environment variables first
load_dotenv()

# Initialize OpenAI client (optional for testing)
openai_client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        openai_client = openai.OpenAI(api_key=api_key)
        print(f"OpenAI client initialized successfully")
    else:
        print("Warning: OPENAI_API_KEY not found in environment")
except Exception as e:
    print(f"Warning: OpenAI client not initialized: {e}")

# Question type definitions with learning science rationale
QUESTION_TYPES = {
    "free_recall": {
        "difficulty": "hard",
        "description": "Open-ended questions that require complete recall from memory",
        "learning_benefit": "Tests deep understanding and complete knowledge retrieval"
    },
    "cued_recall": {
        "difficulty": "medium", 
        "description": "Questions with context clues to guide memory retrieval",
        "learning_benefit": "Scaffolds learning while still testing understanding"
    },
    "recognition": {
        "difficulty": "easy",
        "description": "Multiple choice or yes/no questions that test identification",
        "learning_benefit": "Builds confidence and tests basic knowledge"
    },
    "application": {
        "difficulty": "hard",
        "description": "Questions requiring practical use of knowledge",
        "learning_benefit": "Tests transfer of learning to real-world contexts"
    },
    "connection": {
        "difficulty": "medium-hard",
        "description": "Questions about relationships between concepts",
        "learning_benefit": "Builds schema and conceptual understanding"
    },
    "elaboration": {
        "difficulty": "medium",
        "description": "Questions that build on previous responses",
        "learning_benefit": "Deepens understanding through explanation"
    },
    "analysis": {
        "difficulty": "hard",
        "description": "Questions requiring breaking down concepts into components",
        "learning_benefit": "Develops critical thinking and deep analysis"
    },
    "comparison": {
        "difficulty": "medium-hard", 
        "description": "Questions comparing concepts or approaches",
        "learning_benefit": "Highlights distinctions and similarities"
    }
}


def get_current_session_scores(state: Dict) -> Dict[str, int]:
    """Helper function to extract current session scores"""
    return state.get("scores", {})


def initialize_session_topics(state: Dict) -> None:
    """Initialize topics and current topic tracking"""
    topics = state.get("topics", [])
    if topics:
        state["current_topic_index"] = 0
        state["completed_topics"] = []
        state["topic_scores"] = {}
        state["topic_evaluations"] = {}

def get_current_topic(state: Dict) -> str:
    """Get the current topic being studied"""
    topics = state.get("topics", [])
    current_index = state.get("current_topic_index", 0)
    
    if current_index < len(topics):
        return topics[current_index]
    return None

def get_remaining_topics(state: Dict) -> List[str]:
    """Get remaining topics to be studied"""
    topics = state.get("topics", [])
    current_index = state.get("current_topic_index", 0)
    return topics[current_index + 1:]

def advance_to_next_topic(state: Dict) -> None:
    """Advance to the next topic"""
    current_index = state.get("current_topic_index", 0)
    state["current_topic_index"] = current_index + 1

def build_topic_context(topic: str, topic_source: Dict) -> str:
    """Build context string for a topic"""
    context_parts = [f"Topic: {topic}"]
    
    if topic_source:
        if "name" in topic_source:
            context_parts.append(f"Name: {topic_source['name']}")
        if "difficulty" in topic_source:
            context_parts.append(f"Difficulty: {topic_source['difficulty']}")
        if "context" in topic_source:
            context_parts.append(f"Context: {topic_source['context']}")
    
    return "\n".join(context_parts)

def format_recent_conversation(state: Dict) -> str:
    """Format recent conversation for context"""
    history = state.get("conversation_history", [])
    recent_messages = history[-6:]  # Last 6 messages
    
    formatted = []
    for msg in recent_messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        formatted.append(f"{role.title()}: {content}")
    
    return "\n".join(formatted)


def get_topic_conversation(state: Dict, topic: str) -> List[Dict]:
    """Get conversation messages for a specific topic"""
    history = state.get("conversation_history", [])
    return [msg for msg in history if msg.get("topic") == topic]

def format_topic_conversation_for_evaluation(topic_conversation: List[Dict]) -> str:
    """Format topic conversation for evaluation"""
    if not topic_conversation:
        return "No conversation history for this topic."
    
    formatted = []
    for msg in topic_conversation:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        formatted.append(f"{role.title()}: {content}")
    
    return "\n".join(formatted)

def decide_after_evaluation(state: Dict) -> str:
    """Decide what to do after evaluating a topic"""
    # Move current topic to completed
    current_topic = get_current_topic(state)
    if current_topic:
        completed = state.get("completed_topics", [])
        completed.append(current_topic)
        state["completed_topics"] = completed
        
        # Advance to next topic
        advance_to_next_topic(state)
    
    # Check if there are more topics
    remaining = get_remaining_topics(state)
    if remaining:
        return "next_topic"
    else:
        return "end_session"

def build_conversation_context(state: GraphState, current_topic: str, user_input: str) -> str:
    """Build context for conversation generation"""
    context_parts = [f"Current Topic: {current_topic}"]
    
    # Add user input context
    if user_input:
        context_parts.append(f"Student just said: {user_input}")
    
    # Add message count
    message_count = state.get("message_count", 0)
    context_parts.append(f"Message count: {message_count}")
    
    # Add session type
    session_type = state.get("session_type", "custom_topics")
    context_parts.append(f"Session type: {session_type}")
    
    return "\n".join(context_parts)


