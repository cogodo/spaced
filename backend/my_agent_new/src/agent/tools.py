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

# Phase 5: Advanced Features

def detect_topic_connections(topics: List[str], history: List[Dict]) -> Dict[str, List[str]]:
    """
    Advanced feature: Detect conceptual connections between topics during session
    """
    connections = {}
    
    # Predefined knowledge domain connections
    domain_connections = {
        "python": ["programming", "data science", "machine learning", "web development"],
        "machine learning": ["python", "statistics", "data science", "algorithms", "artificial intelligence"],
        "data science": ["python", "machine learning", "statistics", "data analysis", "visualization"],
        "algorithms": ["programming", "data structures", "computer science", "problem solving"],
        "statistics": ["data science", "machine learning", "probability", "analysis"],
        "web development": ["python", "javascript", "html", "css", "frameworks"],
        "javascript": ["web development", "programming", "frontend", "nodejs"],
        "react": ["javascript", "web development", "frontend", "ui development"],
        "databases": ["sql", "data management", "backend", "storage"],
        "sql": ["databases", "data management", "queries", "data analysis"]
    }
    
    # Find connections based on keywords in answers
    for topic in topics:
        topic_lower = topic.lower()
        related_topics = []
        
        # Check predefined connections
        for key, related in domain_connections.items():
            if key in topic_lower:
                related_topics.extend(related)
        
        # Analyze answers for topic mentions
        topic_answers = [qa['answer'] for qa in history if qa.get('topic') == topic]
        for answer in topic_answers:
            answer_lower = answer.lower()
            for other_topic in topics:
                if other_topic != topic and other_topic.lower() in answer_lower:
                    related_topics.append(other_topic)
        
        connections[topic] = list(set(related_topics))  # Remove duplicates
    
    return connections

def calculate_learning_momentum(scores: Dict[str, int], question_types: List[Dict]) -> float:
    """
    Calculate overall learning momentum during session
    """
    if not scores:
        return 0.0
    
    # Base momentum from average score
    avg_score = sum(scores.values()) / len(scores)
    base_momentum = avg_score / 5.0  # Normalize to 0-1
    
    # Bonus for question variety
    unique_types = len(set(qt.get('type', 'unknown') for qt in question_types))
    variety_bonus = min(unique_types / 8.0, 0.2)  # Up to 20% bonus for using all 8 types
    
    # Bonus for consistent performance
    score_variance = sum((score - avg_score) ** 2 for score in scores.values()) / len(scores)
    consistency_bonus = max(0, 0.15 - (score_variance / 10))  # Less variance = more bonus
    
    momentum = base_momentum + variety_bonus + consistency_bonus
    return min(momentum, 1.0)

def should_extend_session(state: Dict) -> bool:
    """
    Advanced feature: Determine if session should be extended based on performance
    """
    if not state.get("adaptive_session_length"):
        return False
    
    current_scores = get_current_session_scores(state)
    if not current_scores:
        return False
    
    avg_score = sum(current_scores.values()) / len(current_scores)
    struggle_threshold = state.get("struggle_threshold", 2.0)
    
    # Extend if struggling (low scores) and haven't reached max questions
    current_questions = state.get("question_count", 0)
    max_questions = state.get("max_questions", 7)
    
    if avg_score < struggle_threshold and current_questions < max_questions:
        return True
    
    return False

def should_complete_early(state: Dict) -> bool:
    """
    Advanced feature: Determine if session can complete early due to excellent performance
    """
    if not state.get("adaptive_session_length"):
        return False
    
    current_scores = get_current_session_scores(state)
    if not current_scores or len(current_scores) < 2:  # Need at least 2 topics scored
        return False
    
    avg_score = sum(current_scores.values()) / len(current_scores)
    performance_threshold = state.get("performance_threshold", 4.5)
    
    # Complete early if performance is excellent and sufficient questions asked
    current_questions = state.get("question_count", 0)
    min_questions = 2  # Minimum questions before early completion
    
    if avg_score >= performance_threshold and current_questions >= min_questions:
        return True
    
    return False

def get_current_session_scores(state: Dict) -> Dict[str, int]:
    """Helper function to extract current session scores"""
    return state.get("scores", {})

def analyze_answer_confidence(answer: str) -> float:
    """
    Analyze confidence level in user's answer based on linguistic cues
    """
    if not answer or len(answer.strip()) < 10:
        return 0.1
    
    answer_lower = answer.lower()
    
    # Confidence indicators
    confident_phrases = [
        "i know", "definitely", "certainly", "clearly", "obviously", 
        "for sure", "absolutely", "precisely", "exactly", "specifically"
    ]
    
    # Uncertainty indicators
    uncertain_phrases = [
        "i think", "maybe", "possibly", "perhaps", "i'm not sure",
        "i believe", "probably", "might be", "could be", "not certain"
    ]
    
    # Hedging words
    hedging_words = [
        "somewhat", "kind of", "sort of", "more or less", "basically", 
        "essentially", "generally", "typically", "usually", "often"
    ]
    
    confidence_score = 0.5  # Baseline
    
    # Count confident expressions
    for phrase in confident_phrases:
        if phrase in answer_lower:
            confidence_score += 0.1
    
    # Subtract for uncertain expressions
    for phrase in uncertain_phrases:
        if phrase in answer_lower:
            confidence_score -= 0.15
    
    # Subtract slightly for hedging
    for word in hedging_words:
        if word in answer_lower:
            confidence_score -= 0.05
    
    # Length-based confidence (longer explanations often indicate more certainty)
    if len(answer.split()) > 50:
        confidence_score += 0.1
    elif len(answer.split()) < 15:
        confidence_score -= 0.1
    
    # Clamp between 0 and 1
    return max(0.0, min(1.0, confidence_score))

def call_ai_with_json_output(system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Call OpenAI API and get JSON response"""
    if not openai_client:
        raise ValueError("OpenAI client not initialized")
    
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"Error calling AI: {e}")
        return {"error": str(e)}

def call_ai_for_simple_response(system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini") -> str:
    """Call OpenAI API and get simple string response"""
    if not openai_client:
        raise ValueError("OpenAI client not initialized")
    
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error calling AI: {e}")
        return f"Error: {e}"

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

def format_topic_conversation_history(state: Dict, topic: str) -> str:
    """Format conversation history for a specific topic"""
    topic_conversation = get_topic_conversation(state, topic)
    
    formatted = []
    for msg in topic_conversation:
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

def decide_topic_action(state: Dict) -> str:
    """Decide what action to take for the current topic"""
    current_topic = get_current_topic(state)
    if not current_topic:
        return "end_session"
    
    # Check if AI suggested topic completion
    if state.get("ai_suggests_topic_complete", False):
        return "evaluate_topic"
    
    # Check message count for topic
    topic_messages = get_topic_conversation(state, current_topic)
    if len(topic_messages) >= 10:  # Max messages per topic
        return "evaluate_topic"
    
    # Check overall session limits
    total_messages = state.get("message_count", 0)
    max_messages = state.get("max_messages", 20)
    
    if total_messages >= max_messages:
        return "end_session"
    
    return "continue_topic"

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

def analyze_conversation_quality(topic_messages: List[Dict]) -> Dict[str, str]:
    """Analyze the quality of conversation for a topic"""
    if not topic_messages:
        return {
            "engagement": "low",
            "depth": "shallow",
            "interactivity": "minimal"
        }
    
    # Simple heuristics for conversation quality
    total_length = sum(len(msg.get("content", "")) for msg in topic_messages)
    avg_length = total_length / len(topic_messages) if topic_messages else 0
    
    engagement = "high" if len(topic_messages) >= 6 else "medium" if len(topic_messages) >= 3 else "low"
    depth = "deep" if avg_length > 200 else "medium" if avg_length > 100 else "shallow"
    interactivity = "high" if len(topic_messages) >= 8 else "medium" if len(topic_messages) >= 4 else "minimal"
    
    return {
        "engagement": engagement,
        "depth": depth,
        "interactivity": interactivity
    } 