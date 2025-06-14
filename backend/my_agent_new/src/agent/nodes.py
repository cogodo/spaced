from typing import Dict, Any, List
from datetime import datetime, timezone
from agent.state import GraphState
from agent.tools import (
    call_ai_with_json_output, call_ai_for_simple_response,
    initialize_session_topics, get_current_topic, get_remaining_topics,
    advance_to_next_topic, build_topic_context, format_topic_conversation_history,
    get_topic_conversation, format_topic_conversation_for_evaluation
)
from agent.utils.adaptive_intelligence import (
    analyze_user_response_live,
    calculate_adaptive_difficulty,
    determine_adaptive_conversation_strategy,
    update_live_performance_metrics,
    update_learned_preferences,
    calculate_learning_momentum
)
from agent.utils.adaptive_state_integration import (
    auto_save_adaptive_state,
    log_adaptive_decision
)
from agent.utils.firebase_service import firebase_service
import logging

# Configure logging
logger = logging.getLogger(__name__)


def session_initialization_node(state: GraphState) -> Dict[str, Any]:
    """
    Initialize session with welcome message and topic introduction.
    """
    try:
        # Simple welcome message without complex generation to avoid recursion
        topics = state.get("topics", [])
        session_type = state.get("session_type", "custom_topics")
        
        if session_type == "due_items":
            opening_message = f"Great! Let's review your selected topics using spaced repetition. 🧠✨\n\nI'll ask you questions about: {', '.join(topics)}\n\nThis will help reinforce your memory and identify areas that need more attention."
        else:
            opening_message = f"Welcome to your personalized spaced repetition learning session! 🧠✨\n\nI'll help you learn and retain information about: {', '.join(topics)}\n\nLet's start with some questions to assess your current knowledge."
        
        # Set up initial session state
        return {
            "next_question": opening_message,
            "current_topic": topics[0] if topics else None,
            "remaining_topics": topics[1:] if len(topics) > 1 else [],
            "message_count": 1,
            "session_initialized": True
        }
        
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
    """
    AI-driven conversation node with explicit topic management
    Supports both messages key and user_input for compatibility
    """
    # Check for user input from either messages or user_input
    user_input = None
    messages = state.get("messages", [])
    
    # Extract user input from messages if available
    if messages and messages[-1].get("type") == "human":
        user_input = messages[-1].get("content", "")
    elif state.get("user_input"):
        user_input = state.get("user_input")
    
    # Initialize topics if first call
    if user_input is None:
        initialize_session_topics(state)
        opening = generate_topic_aware_opening(state)
        state["message_count"] = 1
        
        # Add to messages
        messages = state.get("messages", [])
        messages.append({
            "type": "ai",
            "content": opening,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "next_question": opening,
            "messages": messages
        }
    
    # Record user's response in both formats
    if user_input:
        # Update messages if not already there
        if not messages or messages[-1].get("type") != "human" or messages[-1].get("content") != user_input:
            messages.append({
                "type": "human", 
                "content": user_input,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Also record in conversation history for backward compatibility
        record_user_response_from_input(state, user_input)
    
    # Clear user input after processing to prevent reprocessing
    state["user_input"] = None
    
    # Get current topic context
    current_topic = get_current_topic(state)
    if not current_topic:
        # No more topics - should end session
        state["session_complete"] = True
        return {"session_complete": True, "messages": messages}
    
    topic_source = state.get("topic_sources", {}).get(current_topic, {})
    
    # Let AI drive conversation with topic awareness
    ai_response = get_topic_aware_response_from_input(state, current_topic, topic_source, user_input)
    
    # Update conversation history
    state["message_count"] = state.get("message_count", 0) + 1
    conversation_history = state.get("conversation_history", [])
    conversation_history.append({
        "role": "assistant",
        "content": ai_response["content"],
        "topic": current_topic,
        "action": ai_response.get("action", "continue"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    state["conversation_history"] = conversation_history
    
    # Add AI response to messages
    messages.append({
        "type": "ai",
        "content": ai_response["content"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Check if AI thinks this topic is complete
    if ai_response.get("action") == "topic_complete":
        state["ai_suggests_topic_complete"] = True
        logger.info(f"AI suggests topic '{current_topic}' is complete")
    else:
        state["ai_suggests_topic_complete"] = False
    
    return {
        "next_question": ai_response["content"],
        "current_topic": current_topic,
        "message_count": state["message_count"],
        "remaining_topics": get_remaining_topics(state),
        "conversation_action": ai_response.get("action", "continue"),
        "messages": messages
    }


def get_topic_aware_response(state: GraphState, current_topic: str, topic_source: Dict) -> Dict:
    """
    Enhanced AI conversation generation with adaptive learning integration
    """
    topic_context = build_topic_context(current_topic, topic_source)
    topic_history = format_topic_conversation_history(state, current_topic)
    user_input = state.get('user_input', '')
    
    # Build conversation context
    conversation_context = build_conversation_context(state, current_topic, user_input)
    
    # Enhanced conversation stage
    conversation_stage = get_conversation_stage(state, current_topic)
    
    system_prompt = f"""
You are an expert AI learning companion with deep expertise in conversational pedagogy, cognitive science, and personalized learning. You're having a natural, adaptive conversation that feels like ChatGPT but is specifically designed to optimize learning through active recall and personalized teaching strategies.

CURRENT CONTEXT:
{conversation_context}

CONVERSATION STAGE: {conversation_stage}

YOUR PEDAGOGICAL APPROACH:

🧠 ADAPTIVE LEARNING SCIENCE INTEGRATION:
- Use rich explanations, analogies, and narrative examples
- Focus on real-world applications and practical examples
- Provide structured, step-by-step exploration when needed
- Allow for discovery, exploration, and pattern recognition

🎯 ACTIVE RECALL TECHNIQUES:
1. **Elaborative Recall**: "Can you walk me through how you understand this concept?"
2. **Analogical Thinking**: "What does this remind you of from your own experience?"
3. **Application Transfer**: "If you had to use this in a real situation, how would you approach it?"
4. **Synthesis Creation**: "How would you explain this to someone who's never encountered it before?"

📊 REAL-TIME LEARNING ADAPTATION:
Continuously assess and adapt based on:
- Confidence signals in their language
- Depth of explanations they provide
- Connection-making ability they demonstrate
- Question quality they ask

🎭 NATURAL CONVERSATION PERSONALITY:
- **Genuinely curious**: "I'm really interested in how you're thinking about this..."
- **Encouraging**: "That's exactly the kind of thinking that shows real understanding!"
- **Intellectually humble**: "That's a perspective I hadn't considered..."
- **Adaptively challenging**: Adjust difficulty based on their demonstrated capabilities

CONVERSATION FLOW GUIDELINES:
1. **Listen Actively**: Respond specifically to what they just said
2. **Challenge Appropriately**: Based on their confidence and understanding level
3. **Build Progressively**: Each exchange should deepen understanding
4. **Connect Meaningfully**: Help them see relationships between concepts

TOPIC COMPLETION INTELLIGENCE:
Make sophisticated decisions about topic readiness based on:
- **Conceptual fluency**: Can they explain clearly and accurately?
- **Application confidence**: Do they show ability to use the knowledge?
- **Connection integration**: Can they relate it to other learning?

If you believe the student has demonstrated good understanding of the current topic and is ready to move on, include "ACTION: topic_complete" at the end of your response.

Respond naturally and conversationally while applying these principles.
"""

    user_prompt = f"""
TOPIC CONTEXT:
{topic_context}

CONVERSATION HISTORY FOR THIS TOPIC:
{topic_history}

STUDENT'S LATEST RESPONSE:
"{user_input}"

Respond as their learning companion, continuing the conversation to deepen their understanding of {current_topic}.
"""

    try:
        response_content = call_ai_for_simple_response(system_prompt, user_prompt)
        
        # Check for topic completion signal
        action = "continue"
        if "ACTION: topic_complete" in response_content:
            action = "topic_complete"
            response_content = response_content.replace("ACTION: topic_complete", "").strip()
        
        return {
            "content": response_content,
            "action": action
        }
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return {
            "content": f"I'd like to continue exploring {current_topic} with you. Could you tell me more about your understanding of this topic?",
            "action": "continue"
        }


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


def get_conversation_stage(state: GraphState, current_topic: str) -> str:
    """Determine the current stage of conversation for the topic"""
    topic_messages = get_topic_conversation(state, current_topic)
    message_count = len(topic_messages)
    
    if message_count == 0:
        return "introduction"
    elif message_count <= 3:
        return "exploration"
    elif message_count <= 6:
        return "deepening"
    else:
        return "synthesis"


def generate_topic_aware_opening(state: GraphState) -> str:
    """Generate an opening message that's aware of the topics"""
    topics = state.get("topics", [])
    session_type = state.get("session_type", "custom_topics")
    
    if not topics:
        return "Hello! I'm ready to help you learn. What would you like to explore today?"
    
    current_topic = topics[0] if topics else "your chosen topic"
    
    if session_type == "due_items":
        return f"Great! Let's review {current_topic}. This is one of your due items for spaced repetition review. What do you remember about {current_topic}?"
    else:
        return f"Wonderful! Let's start exploring {current_topic}. What would you like to know about this topic, or what do you already know that we can build on?"


def record_user_response(state: GraphState):
    """Record the user's response in conversation history"""
    user_input = state.get("user_input", "")
    current_topic = get_current_topic(state)
    
    conversation_history = state.get("conversation_history", [])
    conversation_history.append({
        "role": "user",
        "content": user_input,
        "topic": current_topic,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    state["conversation_history"] = conversation_history


def record_user_response_from_input(state: GraphState, user_input: str):
    """Record the user's response in conversation history from direct input"""
    current_topic = get_current_topic(state)
    
    conversation_history = state.get("conversation_history", [])
    conversation_history.append({
        "role": "user",
        "content": user_input,
        "topic": current_topic,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    state["conversation_history"] = conversation_history


def get_topic_aware_response_from_input(state: GraphState, current_topic: str, topic_source: Dict, user_input: str) -> Dict:
    """
    Enhanced AI conversation generation with adaptive learning integration
    Takes user_input directly as parameter for flexibility
    """
    topic_context = build_topic_context(current_topic, topic_source)
    topic_history = format_topic_conversation_history(state, current_topic)
    
    # Build conversation context
    conversation_context = build_conversation_context(state, current_topic, user_input)
    
    # Enhanced conversation stage
    conversation_stage = get_conversation_stage(state, current_topic)
    
    system_prompt = f"""
You are an expert AI learning companion with deep expertise in conversational pedagogy, cognitive science, and personalized learning. You're having a natural, adaptive conversation that feels like ChatGPT but is specifically designed to optimize learning through active recall and personalized teaching strategies.

CURRENT CONTEXT:
{conversation_context}

CONVERSATION STAGE: {conversation_stage}

YOUR PEDAGOGICAL APPROACH:

🧠 ADAPTIVE LEARNING SCIENCE INTEGRATION:
- Use rich explanations, analogies, and narrative examples
- Focus on real-world applications and practical examples
- Provide structured, step-by-step exploration when needed
- Allow for discovery, exploration, and pattern recognition

🎯 ACTIVE RECALL TECHNIQUES:
1. **Elaborative Recall**: "Can you walk me through how you understand this concept?"
2. **Analogical Thinking**: "What does this remind you of from your own experience?"
3. **Application Transfer**: "If you had to use this in a real situation, how would you approach it?"
4. **Synthesis Creation**: "How would you explain this to someone who's never encountered it before?"

📊 REAL-TIME LEARNING ADAPTATION:
Continuously assess and adapt based on:
- Confidence signals in their language
- Depth of explanations they provide
- Connection-making ability they demonstrate
- Question quality they ask

🎭 NATURAL CONVERSATION PERSONALITY:
- **Genuinely curious**: "I'm really interested in how you're thinking about this..."
- **Encouraging**: "That's exactly the kind of thinking that shows real understanding!"
- **Intellectually humble**: "That's a perspective I hadn't considered..."
- **Adaptively challenging**: Adjust difficulty based on their demonstrated capabilities

CONVERSATION FLOW GUIDELINES:
1. **Listen Actively**: Respond specifically to what they just said
2. **Challenge Appropriately**: Based on their confidence and understanding level
3. **Build Progressively**: Each exchange should deepen understanding
4. **Connect Meaningfully**: Help them see relationships between concepts

TOPIC COMPLETION INTELLIGENCE:
Make sophisticated decisions about topic readiness based on:
- **Conceptual fluency**: Can they explain clearly and accurately?
- **Application confidence**: Do they show ability to use the knowledge?
- **Connection integration**: Can they relate it to other learning?

If you believe the student has demonstrated good understanding of the current topic and is ready to move on, include "ACTION: topic_complete" at the end of your response.

Respond naturally and conversationally while applying these principles.
"""

    user_prompt = f"""
TOPIC CONTEXT:
{topic_context}

CONVERSATION HISTORY FOR THIS TOPIC:
{topic_history}

STUDENT'S LATEST RESPONSE:
"{user_input}"

Respond as their learning companion, continuing the conversation to deepen their understanding of {current_topic}.
"""

    try:
        response_content = call_ai_for_simple_response(system_prompt, user_prompt)
        
        # Check for topic completion signal
        action = "continue"
        if "ACTION: topic_complete" in response_content:
            action = "topic_complete"
            response_content = response_content.replace("ACTION: topic_complete", "").strip()
        
        return {
            "content": response_content,
            "action": action
        }
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return {
            "content": f"I'd like to continue exploring {current_topic} with you. Could you tell me more about your understanding of this topic?",
            "action": "continue"
        }


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


def complete_session_with_topic_scores(state: GraphState) -> Dict[str, Any]:
    """
    Complete the session and provide comprehensive summary
    """
    try:
        completed_topics = state.get("completed_topics", [])
        topic_scores = state.get("topic_scores", {})
        topic_evaluations = state.get("topic_evaluations", {})
        conversation_history = state.get("conversation_history", [])
        
        # Calculate session metrics
        total_topics = len(completed_topics)
        avg_score = sum(topic_scores.values()) / len(topic_scores) if topic_scores else 0
        total_messages = len(conversation_history)
        
        # Generate session summary
        session_summary = {
            "session_id": state.get("session_id", "unknown"),
            "completed_topics": completed_topics,
            "topic_scores": topic_scores,
            "topic_evaluations": topic_evaluations,
            "total_topics_covered": total_topics,
            "average_score": round(avg_score, 2),
            "total_messages": total_messages,
            "session_end_time": datetime.now(timezone.utc).isoformat(),
            "session_type": state.get("session_type", "custom_topics")
        }
        
        # Generate completion message
        if total_topics > 0:
            score_text = f"average score of {avg_score:.1f}/5"
            topic_list = ", ".join(completed_topics)
            completion_message = f"Great session! You covered {total_topics} topic(s): {topic_list}. You achieved an {score_text}. "
            
            if avg_score >= 4.0:
                completion_message += "Excellent understanding demonstrated! 🌟"
            elif avg_score >= 3.0:
                completion_message += "Good progress made! Keep up the great work! 📚"
            else:
                completion_message += "You're building your understanding. Consider reviewing these topics again soon. 💪"
        else:
            completion_message = "Thanks for the session! Feel free to start a new session anytime."
        
        # Mark session as complete
        state["session_complete"] = True
        state["session_summary"] = session_summary
        
        logger.info(f"Session completed: {total_topics} topics, avg score: {avg_score:.2f}")
        
        return {
            "session_complete": True,
            "session_summary": session_summary,
            "completion_message": completion_message,
            "next_question": completion_message
        }
        
    except Exception as e:
        logger.error(f"Error completing session: {e}")
        return {
            "session_complete": True,
            "session_summary": {"error": str(e)},
            "completion_message": "Session completed. Thank you for learning with me!",
            "next_question": "Session completed. Thank you for learning with me!"
        } 