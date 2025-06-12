import random
from typing import Dict, List, Tuple
import re
from datetime import datetime, timezone
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Initialize OpenAI LLM lazily to avoid import errors when API key is not set
_llm = None

def get_llm():
    """Get or create the OpenAI LLM instance"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    return _llm

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
        "i think", "maybe", "probably", "perhaps", "might be", 
        "not sure", "i guess", "possibly", "could be", "seems like"
    ]
    
    # Hedging words
    hedging_words = [
        "sort of", "kind of", "somewhat", "rather", "quite", 
        "fairly", "pretty much", "more or less"
    ]
    
    # Calculate confidence score
    confidence_score = 0.5  # Base confidence
    
    # Boost for confident language
    for phrase in confident_phrases:
        if phrase in answer_lower:
            confidence_score += 0.1
    
    # Reduce for uncertain language
    for phrase in uncertain_phrases:
        if phrase in answer_lower:
            confidence_score -= 0.15
    
    # Slight reduction for hedging
    for word in hedging_words:
        if word in answer_lower:
            confidence_score -= 0.05
    
    # Length and detail bonus
    if len(answer) > 100:
        confidence_score += 0.1
    if len(answer) > 200:
        confidence_score += 0.1
    
    return max(0.0, min(1.0, confidence_score))

def generate_cross_topic_insights(state: Dict) -> List[Dict[str, any]]:
    """
    Generate insights about connections discovered during the session
    """
    insights = []
    topic_connections = state.get("topic_connections", {})
    history = state.get("history", [])
    
    if not topic_connections or not history:
        return insights
    
    # Look for users mentioning connections in their answers
    for qa in history:
        answer = qa.get("answer", "").lower()
        current_topic = qa.get("topic", "")
        
        # Check if user mentioned other topics from the session
        for other_topic in state.get("topics", []):
            if other_topic != current_topic and other_topic.lower() in answer:
                insights.append({
                    "type": "user_connection",
                    "from_topic": current_topic,
                    "to_topic": other_topic,
                    "context": qa.get("answer", "")[:100] + "...",
                    "discovery_moment": qa.get("question", "")
                })
    
    # Generate system-detected patterns
    topics = state.get("topics", [])
    for topic in topics:
        related = topic_connections.get(topic, [])
        if related:
            insights.append({
                "type": "system_connection",
                "topic": topic,
                "related_topics": related,
                "strength": len(related),
                "recommendation": f"Consider studying {', '.join(related[:3])} to reinforce {topic}"
            })
    
    return insights

def predict_retention(state: Dict) -> Dict[str, float]:
    """
    Predict retention likelihood for each topic based on session performance
    """
    predictions = {}
    scores = state.get("scores", {})
    confidence_scores = state.get("answer_confidence_scores", [])
    question_types = state.get("question_types", [])
    
    for topic, score in scores.items():
        # Base retention from score
        base_retention = score / 5.0
        
        # Get confidence for this topic's answers
        topic_confidences = []
        for i, qt in enumerate(question_types):
            if qt.get("topic") == topic and i < len(confidence_scores):
                topic_confidences.append(confidence_scores[i])
        
        confidence_factor = sum(topic_confidences) / len(topic_confidences) if topic_confidences else 0.5
        
        # Question type diversity for this topic
        topic_question_types = [qt.get("type") for qt in question_types if qt.get("topic") == topic]
        type_diversity = len(set(topic_question_types)) / 8.0  # Normalize by total types
        
        # Final retention prediction
        retention = (base_retention * 0.6) + (confidence_factor * 0.3) + (type_diversity * 0.1)
        predictions[topic] = min(1.0, max(0.0, retention))
    
    return predictions

def generate_next_session_recommendations(state: Dict) -> Dict[str, any]:
    """
    Generate intelligent recommendations for the user's next study session
    """
    scores = state.get("scores", {})
    retention_predictions = state.get("retention_prediction", {})
    topic_connections = state.get("topic_connections", {})
    
    if not scores:
        return {"recommendation": "Start with custom topics to build momentum"}
    
    # Find topics that need review
    struggling_topics = [topic for topic, score in scores.items() if score < 3]
    mastered_topics = [topic for topic, score in scores.items() if score >= 4]
    
    recommendations = {
        "session_type": "due_items" if state.get("session_type") == "due_items" else "custom_topics",
        "priority_topics": struggling_topics[:3],  # Top 3 struggling topics
        "reinforcement_topics": mastered_topics[:2],  # Keep sharp on mastered topics
        "estimated_duration": estimate_session_duration(state),
        "focus_areas": [],
        "learning_strategy": ""
    }
    
    # Specific focus recommendations
    if struggling_topics:
        recommendations["focus_areas"].append("Review fundamentals")
        recommendations["learning_strategy"] = "Focus on understanding core concepts with easier question types"
    
    if len(mastered_topics) > len(struggling_topics):
        recommendations["focus_areas"].append("Explore advanced applications")
        recommendations["learning_strategy"] = "Challenge yourself with application and analysis questions"
    
    # Connection-based recommendations
    if topic_connections:
        connected_topics = []
        for topic in struggling_topics:
            connected_topics.extend(topic_connections.get(topic, []))
        
        if connected_topics:
            recommendations["connected_learning"] = list(set(connected_topics))[:3]
    
    return recommendations

def estimate_session_duration(state: Dict) -> int:
    """
    Estimate optimal duration for next session based on performance
    """
    scores = state.get("scores", {})
    
    if not scores:
        return 15  # Default 15 minutes
    
    avg_score = sum(scores.values()) / len(scores)
    
    # Adjust duration based on performance
    if avg_score < 2.5:
        return 20  # Longer sessions for struggling areas
    elif avg_score > 4.0:
        return 10  # Shorter, focused sessions for mastered areas
    else:
        return 15  # Standard duration

def determine_completion_reason(state: Dict) -> str:
    """
    Determine why the session ended for analytics
    """
    if should_complete_early(state):
        return "performance_achieved"
    elif state.get("question_count", 0) >= state.get("max_questions", 7):
        return "max_questions_reached"
    elif state.get("current_topic_index", 0) >= len(state.get("topics", [])):
        return "all_topics_completed"
    else:
        return "standard_completion"

# Enhanced existing functions for Phase 5

def get_task_difficulty(state: Dict, topic: str) -> float:
    """Get FSRS difficulty for a task if available"""
    if state.get("session_type") == "due_items" and state.get("tasks"):
        for task in state["tasks"]:
            if task.task_name == topic:
                return task.difficulty
    return 0.5  # Default difficulty for custom topics

def get_task_context(state: Dict, topic: str) -> Dict:
    """Get additional FSRS context for a task"""
    if state.get("session_type") == "due_items" and state.get("tasks"):
        for task in state["tasks"]:
            if task.task_name == topic:
                return {
                    "difficulty": task.difficulty,
                    "days_overdue": task.days_overdue,
                    "stability": task.stability,
                    "repetition": task.repetition,
                    "previous_interval": task.previous_interval
                }
    return {"difficulty": 0.5, "days_overdue": 0, "stability": 1.0, "repetition": 0, "previous_interval": 1}

def select_question_type(difficulty: float, question_count: int, topic_history: List[Dict]) -> str:
    """
    Enhanced question type selection with Phase 5 adaptive features
    """
    
    # Get previously used question types for this topic
    used_types = [qa.get('question_type', 'free_recall') for qa in topic_history]
    
    # Define question pools based on difficulty
    if difficulty >= 0.8:
        # Very high difficulty - prioritize easiest question types
        primary_pool = ["recognition", "cued_recall", "elaboration"]
        secondary_pool = ["comparison", "connection"]
    elif difficulty >= 0.6:
        # High difficulty - mostly easier types with some medium
        primary_pool = ["recognition", "cued_recall", "elaboration", "comparison"]
        secondary_pool = ["connection", "application"]
    elif difficulty >= 0.4:
        # Medium difficulty - balanced mix, avoid hardest
        primary_pool = ["cued_recall", "elaboration", "comparison", "connection"]
        secondary_pool = ["recognition", "application", "analysis"]
    elif difficulty >= 0.2:
        # Low difficulty - harder questions with some support
        primary_pool = ["application", "connection", "analysis", "comparison"]
        secondary_pool = ["free_recall", "cued_recall", "elaboration"]
    else:
        # Very low difficulty - hardest questions to challenge learning
        primary_pool = ["free_recall", "application", "analysis"]
        secondary_pool = ["connection", "comparison", "cued_recall"]
    
    # Progression: start easier, get progressively harder within bounds
    if question_count == 1:
        # First question - be more gentle
        available_types = primary_pool + secondary_pool
        # Prefer easier types for first question
        if "recognition" in available_types:
            return "recognition"
        elif "cued_recall" in available_types:
            return "cued_recall"
    
    # Avoid repeating the same type consecutively
    if used_types:
        last_type = used_types[-1]
        available_types = [t for t in primary_pool + secondary_pool if t != last_type]
    else:
        available_types = primary_pool + secondary_pool
    
    # Ensure variety - avoid overusing any single type
    type_counts = {t: used_types.count(t) for t in QUESTION_TYPES.keys()}
    min_used_count = min(type_counts.values()) if type_counts else 0
    
    # Prefer less-used types
    preferred_types = [t for t in available_types if type_counts.get(t, 0) <= min_used_count]
    
    if preferred_types:
        # Weight selection toward primary pool
        if len([t for t in preferred_types if t in primary_pool]) > 0:
            pool_choices = [t for t in preferred_types if t in primary_pool]
        else:
            pool_choices = preferred_types
        return random.choice(pool_choices)
    else:
        # Fallback to any available type
        return random.choice(available_types) if available_types else "cued_recall"

def generate_question_by_type(topic: str, question_type: str, question_count: int, history: List[Dict], task_context: Dict = None) -> str:
    """Enhanced question generation with more variety and context awareness"""
    
    # Extract key info for context-aware questions
    overdue_days = task_context.get("days_overdue", 0) if task_context else 0
    repetition = task_context.get("repetition", 0) if task_context else 0
    
    if question_type == "free_recall":
        if repetition > 3:
            questions = [
                f"From memory, explain everything you know about {topic}.",
                f"Without looking anything up, describe {topic} comprehensively.",
                f"Give me a complete overview of {topic} from your memory.",
                f"Recall and explain all aspects of {topic}."
            ]
        else:
            questions = [
                f"Tell me what you remember about {topic}.",
                f"What do you know about {topic}?",
                f"Explain {topic} to me.",
                f"Describe your understanding of {topic}."
            ]
    
    elif question_type == "cued_recall":
        if overdue_days > 7:
            questions = [
                f"It's been a while since you've reviewed {topic}. What key points do you remember?",
                f"When you think about {topic}, what main concepts come to mind?",
                f"If you had to teach {topic} to someone, what would you focus on?",
                f"What are the most important aspects of {topic} that you can recall?"
            ]
        else:
            questions = [
                f"In the context of {topic}, what key principles should you remember?",
                f"When working with {topic}, what approach would you take?",
                f"What essential elements make up {topic}?",
                f"If someone mentioned {topic}, what would you think of first?"
            ]
    
    elif question_type == "recognition":
        questions = [
            f"Is {topic} primarily theoretical or practical in nature?",
            f"True or false: {topic} is commonly used for problem-solving?",
            f"Would you categorize {topic} as beginner-friendly or advanced?",
            f"Does {topic} relate more to planning or execution?",
            f"Is {topic} something you'd use daily or occasionally?"
        ]
    
    elif question_type == "application":
        questions = [
            f"Give me a practical example of how you'd use {topic}.",
            f"How would you apply {topic} to solve a real problem?",
            f"What steps would you take to implement {topic} in practice?",
            f"Describe a scenario where {topic} would be valuable.",
            f"How could {topic} improve an existing process or system?"
        ]
    
    elif question_type == "connection":
        questions = [
            f"How does {topic} relate to other concepts you've learned?",
            f"What connections exist between {topic} and similar topics?",
            f"How does {topic} fit into the broader domain?",
            f"What other topics work well together with {topic}?",
            f"How might {topic} influence or be influenced by related concepts?"
        ]
    
    elif question_type == "elaboration":
        if history:
            last_answer = history[-1].get("answer", "")
            questions = [
                f"You mentioned {topic}. Can you elaborate on that further?",
                f"Tell me more about what you just said regarding {topic}.",
                f"Can you expand on your previous point about {topic}?",
                f"What additional details about {topic} would be helpful to know?"
            ]
        else:
            questions = [
                f"Can you provide more specific details about {topic}?",
                f"What nuances or subtleties exist within {topic}?",
                f"Are there important details about {topic} worth mentioning?",
                f"What depth of knowledge do you have about {topic}?"
            ]
    
    elif question_type == "analysis":
        questions = [
            f"Break down {topic} into its key components.",
            f"What are the main parts or elements of {topic}?",
            f"How would you analyze the structure of {topic}?",
            f"What factors make {topic} work effectively?",
            f"Analyze the strengths and weaknesses of {topic}."
        ]
    
    elif question_type == "comparison":
        questions = [
            f"How does {topic} compare to similar concepts?",
            f"What makes {topic} different from alternatives?",
            f"Compare and contrast {topic} with related approaches.",
            f"What are the advantages of {topic} over other options?",
            f"In what ways is {topic} similar to or different from what you've learned before?"
        ]
    
    else:
        # Fallback to cued recall
        questions = [f"What do you remember about {topic}?"]
    
    # Avoid repeating exact questions
    asked_questions = [qa.get('question', '') for qa in history]
    available_questions = [q for q in questions if q not in asked_questions]
    
    if available_questions:
        selected = random.choice(available_questions)
    else:
        # If all questions were used, add variation
        selected = f"{random.choice(questions)} (Question #{question_count})"
    
    return selected

def analyze_answer_quality(answer: str) -> Dict[str, float]:
    """Analyze answer quality using multiple heuristics"""
    if not answer or len(answer.strip()) < 10:
        return {"length": 0, "detail": 0, "structure": 0, "examples": 0, "keywords": 0}
    
    answer_lower = answer.lower()
    
    # Length analysis
    length_score = min(len(answer) / 200, 1.0)  # Normalize to 200 chars = 1.0
    
    # Detail indicators
    detail_keywords = [
        'because', 'therefore', 'however', 'although', 'specifically', 'for example',
        'such as', 'including', 'particularly', 'especially', 'moreover', 'furthermore'
    ]
    detail_score = min(sum(1 for kw in detail_keywords if kw in answer_lower) / 5, 1.0)
    
    # Structure indicators
    structure_keywords = [
        'first', 'second', 'third', 'next', 'finally', 'in conclusion',
        'main', 'primary', 'key', 'important', 'essential', 'crucial'
    ]
    structure_score = min(sum(1 for kw in structure_keywords if kw in answer_lower) / 3, 1.0)
    
    # Examples and specificity
    example_indicators = ['example', 'instance', 'case', 'scenario', 'situation', 'like']
    examples_score = min(sum(1 for ind in example_indicators if ind in answer_lower) / 2, 1.0)
    
    # Domain-specific keywords (shows depth)
    domain_keywords = [
        'process', 'method', 'approach', 'technique', 'strategy', 'principle',
        'concept', 'theory', 'framework', 'model', 'system', 'implementation'
    ]
    keywords_score = min(sum(1 for kw in domain_keywords if kw in answer_lower) / 4, 1.0)
    
    return {
        "length": length_score,
        "detail": detail_score,
        "structure": structure_score,
        "examples": examples_score,
        "keywords": keywords_score
    }

def calculate_adaptive_score(topic: str, topic_qa: List[Dict], task_context: Dict, question_types: List[Dict]) -> float:
    """Calculate score with difficulty adaptation and question type weighting"""
    if not topic_qa:
        return 0.0
    
    difficulty = task_context.get("difficulty", 0.5)
    days_overdue = task_context.get("days_overdue", 0)
    
    total_weighted_score = 0
    total_weight = 0
    
    for i, qa in enumerate(topic_qa):
        answer = qa.get('answer', '')
        
        # Find corresponding question type
        question_type_info = None
        for qt in question_types:
            if qt['topic'] == topic and qt['question'] == qa.get('question', ''):
                question_type_info = qt
                break
        
        question_type = question_type_info['type'] if question_type_info else 'cued_recall'
        
        # Analyze answer quality
        quality_metrics = analyze_answer_quality(answer)
        
        # Base score from quality metrics
        base_score = (
            quality_metrics['length'] * 1.0 +
            quality_metrics['detail'] * 1.5 +
            quality_metrics['structure'] * 1.0 +
            quality_metrics['examples'] * 1.2 +
            quality_metrics['keywords'] * 0.8
        ) / 5.5  # Normalize to 0-1
        
        # Question type difficulty weighting
        type_weights = {
            "recognition": 0.7,      # Easier questions get lower weight
            "cued_recall": 0.9,
            "elaboration": 1.0,
            "comparison": 1.1,
            "connection": 1.2,
            "application": 1.3,
            "analysis": 1.4,
            "free_recall": 1.5       # Harder questions get higher weight
        }
        
        question_weight = type_weights.get(question_type, 1.0)
        
        # Difficulty adaptation: be more generous with high-difficulty tasks
        if difficulty >= 0.7:
            difficulty_bonus = 0.3  # Significant bonus for struggling topics
        elif difficulty >= 0.5:
            difficulty_bonus = 0.1  # Small bonus for medium difficulty
        else:
            difficulty_bonus = 0.0  # No bonus for easy topics
        
        # Overdue penalty/adjustment
        if days_overdue > 14:
            overdue_adjustment = 0.2  # More generous for very overdue items
        elif days_overdue > 7:
            overdue_adjustment = 0.1  # Slightly more generous
        else:
            overdue_adjustment = 0.0
        
        # Calculate weighted score for this answer
        adjusted_score = min(base_score + difficulty_bonus + overdue_adjustment, 1.0)
        weighted_score = adjusted_score * question_weight
        
        total_weighted_score += weighted_score
        total_weight += question_weight
    
    # Final score (0-5 scale)
    if total_weight > 0:
        normalized_score = total_weighted_score / total_weight
        final_score = round(normalized_score * 5)
        return max(0, min(5, final_score))
    else:
        return 0

def call_main_llm(state: Dict) -> str:
    """
    Enhanced question generator with Phase 5 adaptive features using OpenAI.
    
    Features:
    - FSRS difficulty-based question type selection
    - Progressive question difficulty
    - Context-aware question generation
    - Question type variety enforcement
    - Overdue-sensitive questioning
    - Phase 5: Adaptive session length consideration
    """
    current_idx = state["current_topic_index"]
    topic = state["topics"][current_idx]
    history = state["history"]
    question_count = state["question_count"]
    session_type = state.get("session_type", "custom_topics")

    # Get topic-specific history and context
    topic_history = [qa for qa in history if qa.get('topic') == topic]
    task_context = get_task_context(state, topic)
    difficulty = task_context["difficulty"]
    
    # Phase 5: Check for adaptive session completion
    if should_complete_early(state):
        state["session_completion_reason"] = "performance_achieved"
        return None  # Signal early completion
    
    # Select adaptive question type
    question_type = select_question_type(difficulty, question_count, topic_history)
    
    # Build context for OpenAI
    system_prompt = f"""You are an expert learning coach specializing in spaced repetition and adaptive questioning.

Your task: Generate a {question_type} question about "{topic}" for a learner.

Question Type Guidelines:
- free_recall: Open-ended questions requiring complete recall from memory
- cued_recall: Questions with context clues to guide memory retrieval  
- recognition: Multiple choice or yes/no questions for identification
- application: Questions requiring practical use of knowledge
- connection: Questions about relationships between concepts
- elaboration: Questions that build on previous responses
- analysis: Questions requiring breaking down concepts into components
- comparison: Questions comparing concepts or approaches

Context:
- This is question #{question_count} about {topic}
- Session type: {session_type}
- Difficulty level: {difficulty:.2f} (0=easy, 1=hard)
- Previous questions asked: {len(topic_history)}

Session History:
{chr(10).join([f"Q: {qa.get('question', 'N/A')[:100]}..." for qa in topic_history[-3:]])}

Generate ONE focused question that:
1. Matches the {question_type} question type exactly
2. Is appropriate for difficulty level {difficulty:.2f}
3. Avoids repeating previous questions
4. Helps assess the learner's understanding of {topic}

Return ONLY the question text, nothing else."""

    if task_context.get("days_overdue", 0) > 7:
        system_prompt += f"\n\nNote: This topic is {task_context['days_overdue']} days overdue - consider gentler questioning."

    try:
        messages = [SystemMessage(content=system_prompt)]
        response = get_llm().invoke(messages)
        question = response.content.strip()
        
        # Phase 5: Track difficulty progression
        if 'question_difficulty_progression' not in state:
            state['question_difficulty_progression'] = []
        state['question_difficulty_progression'].append(difficulty)
        
        # Log difficulty adaptation for monitoring
        if session_type == "due_items":
            overdue_info = f", {task_context['days_overdue']} days overdue" if task_context['days_overdue'] > 0 else ""
            print(f"Generated {question_type} question for '{topic}' (difficulty: {difficulty:.2f}{overdue_info})")
        
        # Store question type in state for evaluation
        if 'question_types' not in state:
            state['question_types'] = []
        state['question_types'].append({
            'topic': topic,
            'type': question_type,
            'question': question,
            'difficulty_context': task_context
        })
        
        return question
        
    except Exception as e:
        print(f"Error calling OpenAI for question generation: {e}")
        # Fallback to deterministic question generation
        return generate_question_by_type(topic, question_type, question_count, topic_history, task_context)

def call_evaluator_llm(state: Dict) -> Dict[str, int]:
    """
    Enhanced evaluator with sophisticated FSRS-aware scoring and Phase 5 analytics using OpenAI.
    
    Features:
    - Question type difficulty weighting
    - FSRS difficulty adaptation (more generous for struggling topics)
    - Overdue task considerations
    - Multi-factor answer quality analysis
    - Consistency across question types
    - Phase 5: Advanced analytics and insights
    """
    topics = state.get("topics", [])
    history = state.get("history", [])
    session_type = state.get("session_type", "custom_topics")
    question_types = state.get("question_types", [])

    # Ensure we have topics to evaluate
    if not topics:
        raise ValueError("No topics found for evaluation")

    scores = {}
    
    # Phase 5: Enhanced analytics initialization
    if 'answer_confidence_scores' not in state:
        state['answer_confidence_scores'] = []
    
    for topic in topics:
        # Get all Q&A pairs for this topic
        topic_qa = [qa for qa in history if qa.get('topic') == topic]
        
        if not topic_qa:
            scores[topic] = 0
            continue
        
        # Phase 5: Analyze answer confidence for each response
        for qa in topic_qa:
            confidence = analyze_answer_confidence(qa.get('answer', ''))
            state['answer_confidence_scores'].append(confidence)
        
        # Get task context for adaptive scoring
        task_context = get_task_context(state, topic)
        difficulty = task_context.get("difficulty", 0.5)
        days_overdue = task_context.get("days_overdue", 0)
        
        # Build evaluation prompt for OpenAI
        qa_text = ""
        for i, qa in enumerate(topic_qa, 1):
            question_type = "unknown"
            for qt in question_types:
                if qt.get('topic') == topic and qt.get('question') == qa.get('question'):
                    question_type = qt.get('type', 'unknown')
                    break
            
            qa_text += f"\nQ{i} ({question_type}): {qa.get('question', 'N/A')}\n"
            qa_text += f"A{i}: {qa.get('answer', 'N/A')}\n"
        
        system_prompt = f"""You are an expert learning assessment specialist. Evaluate a learner's understanding of "{topic}" based on their Q&A session.

Context:
- Topic: {topic}
- Session type: {session_type}
- Topic difficulty: {difficulty:.2f} (0=easy, 1=hard)
- Days overdue: {days_overdue}
- Total questions: {len(topic_qa)}

Question-Answer Session:
{qa_text}

Evaluation Criteria:
1. Accuracy of responses
2. Depth of understanding shown
3. Use of correct terminology
4. Ability to explain concepts
5. Recognition of key principles

Scoring Guidelines:
- 5: Excellent understanding, comprehensive and accurate responses
- 4: Good understanding, mostly accurate with minor gaps
- 3: Adequate understanding, some inaccuracies or incomplete responses  
- 2: Limited understanding, significant gaps or errors
- 1: Poor understanding, mostly incorrect or vague responses
- 0: No understanding demonstrated

Special Considerations:
- For high difficulty topics ({difficulty:.2f}), be more generous with scoring
- For overdue topics ({days_overdue} days), focus on retention rather than perfection
- Weight harder question types (analysis, application) more heavily than easier ones (recognition)

Return ONLY a single integer score from 0-5 for this topic. No explanation needed."""

        try:
            messages = [SystemMessage(content=system_prompt)]
            response = get_llm().invoke(messages)
            score_text = response.content.strip()
            
            # Extract score from response
            try:
                score = int(score_text)
                score = max(0, min(5, score))  # Ensure score is in valid range
            except ValueError:
                # Fallback if OpenAI doesn't return a clean integer
                print(f"Warning: OpenAI returned non-integer score for {topic}: {score_text}")
                score = calculate_adaptive_score(topic, topic_qa, task_context, question_types)
            
            scores[topic] = score
            
            # Log scoring details for debugging
            if session_type == "due_items":
                print(f"Scored '{topic}': {score}/5 (difficulty: {difficulty:.2f}, overdue: {days_overdue} days)")
                
        except Exception as e:
            print(f"Error calling OpenAI for evaluation of {topic}: {e}")
            # Fallback to algorithmic scoring
            score = calculate_adaptive_score(topic, topic_qa, task_context, question_types)
            scores[topic] = score
    
    # Phase 5: Generate advanced analytics (with error handling)
    try:
        state["topic_connections"] = detect_topic_connections(topics, history)
        state["cross_topic_insights"] = generate_cross_topic_insights(state)
        state["learning_momentum"] = calculate_learning_momentum(scores, question_types)
        state["retention_prediction"] = predict_retention(state)
        state["recommended_next_session"] = generate_next_session_recommendations(state)
        state["session_completion_reason"] = determine_completion_reason(state)
        
        # Calculate learning velocity (improvement rate during session)
        if len(scores) > 1:
            score_values = list(scores.values())
            state["learning_velocity"] = (score_values[-1] - score_values[0]) / len(score_values)
        else:
            state["learning_velocity"] = 0.0
    except Exception as e:
        print(f"Warning: Error generating analytics: {e}")
        # Set default values for analytics only - scores are still valid
        state["learning_momentum"] = 0.0
        state["learning_velocity"] = 0.0
    
    if not scores:
        raise ValueError("Evaluation failed: No valid scores generated")
    
    return scores

# Keep the original functions commented out for when API keys are available
"""
Original OpenAI-powered implementations would go here with similar enhancements:
- FSRS difficulty context in prompts
- Question type selection based on difficulty
- Enhanced evaluation criteria
- Task-specific scoring adjustments
- Phase 5: Advanced analytics and adaptive features

For production, these mock functions should be replaced with:
1. call_main_llm_openai(state) - with FSRS-aware prompts and Phase 5 features
2. call_evaluator_llm_openai(state) - with task difficulty context and advanced analytics
"""
