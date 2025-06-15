from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from agent.state import GraphState
from agent.tools import (
    get_current_topic,build_topic_context,
    get_topic_conversation, format_topic_conversation_for_evaluation
)
from agent.utils.firebase_service import firebase_service
import logging

# Configure logging
logger = logging.getLogger(__name__)

#todo - need a questions tool node - we need a tool for question generation, and
# a tool for question retrieval
# really it's a router that first checks if there are questions that exist, then if they 
# do, go to a retriever tool to get stuff from firebase, and if they don't, go to a llm node
# that's prompted to make more good questions. Then, go to another tool node to
# put these in firebase and then retrieve them tool call
def review_questions_node(state: GraphState) -> Dict[str, Any]:
    """
    Given the topics, retrieve or generate questions that promote active recall!
    """
    try:
        topics = state.get("topics", [])

        return {}
        
    except Exception as e:
        logger.error(f"Error in session initialization: {e}")
        return {
            "next_question": "Welcome! Let's start learning together.",
            "current_topic": state.get("topics", [])[0] if state.get("topics") else None,
            "remaining_topics": state.get("topics", [])[1:] if len(state.get("topics", [])) > 1 else [],
            "message_count": 1,
            "session_initialized": True
        }


def conversation_node(state: GraphState) -> Dict[str, Any]:
    return NotImplemented


def evaluate_topic_node(state: GraphState) -> Dict[str, Any]:
    """
    Evaluate learning for the current topic and assign a score
    """
    current_topic = get_current_topic(state)
    if not current_topic:
        return {"error": "No current topic to evaluate"}
    
    try:
        # Get conversation for this topic
        topic_conversation = get_topic_conversation(state, current_topic)
        topic_source = state.get("topic_sources", {}).get(current_topic, {})
        
        # Build evaluation context
        conversation_formatted = format_topic_conversation_for_evaluation(topic_conversation)
        topic_context = build_topic_context(current_topic, topic_source)
        
        # Create evaluation prompt
        system_prompt = """
You are an expert learning assessment AI. Your task is to evaluate a student's understanding based on their conversation about a topic.

Evaluate the student's performance on a scale of 0-5:
- 0: No understanding demonstrated
- 1: Minimal understanding, significant gaps
- 2: Basic understanding, many gaps
- 3: Developing understanding, some gaps
- 4: Good understanding, minor gaps  
- 5: Excellent understanding, comprehensive grasp

Consider:
- Accuracy of explanations
- Depth of understanding
- Ability to make connections
- Confidence in responses
- Quality of questions asked

Provide your evaluation as JSON:
{
    "score": 4,
    "understanding_level": "good",
    "strengths": ["Clear explanations", "Good examples"],
    "areas_for_improvement": ["Could explore connections more"],
    "confidence_assessment": "high",
    "recommendation": "Ready to move to next topic"
}
"""

        user_prompt = f"""
TOPIC: {current_topic}

TOPIC CONTEXT:
{topic_context}

CONVERSATION:
{conversation_formatted}

Evaluate this student's understanding of {current_topic} based on the conversation.
"""

        evaluation = call_ai_with_json_output(system_prompt, user_prompt)
        
        # Validate evaluation structure
        score = evaluation.get("score", 3)
        if not isinstance(score, (int, float)) or score < 0 or score > 5:
            score = 3
        
        # Store evaluation
        topic_evaluations = state.get("topic_evaluations", {})
        topic_evaluations[current_topic] = evaluation
        state["topic_evaluations"] = topic_evaluations
        
        # Store score
        topic_scores = state.get("topic_scores", {})
        topic_scores[current_topic] = int(score)
        state["topic_scores"] = topic_scores
        
        logger.info(f"Evaluated topic '{current_topic}': score={score}")
        
        return {
            "topic_evaluated": current_topic,
            "score": score,
            "evaluation": evaluation,
            "topic_scores": topic_scores
        }
        
    except Exception as e:
        logger.error(f"Error evaluating topic {current_topic}: {e}")
        # Fallback evaluation
        fallback_score = 3
        topic_scores = state.get("topic_scores", {})
        topic_scores[current_topic] = fallback_score
        state["topic_scores"] = topic_scores
        
        return {
            "topic_evaluated": current_topic,
            "score": fallback_score,
            "evaluation": {"error": str(e)},
            "topic_scores": topic_scores
        }


