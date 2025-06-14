"""
Phase 4: Real-Time Adaptive Intelligence
Advanced AI system for live learning optimization and personalization
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import json
import asyncio
from statistics import mean, stdev

from agent.tools import call_ai_with_json_output, call_ai_for_simple_response
from agent.state import GraphState

logger = logging.getLogger(__name__)

# ================================================================================================
# REAL-TIME ANALYSIS ENGINE
# ================================================================================================

async def analyze_user_response_live(user_input: str, state: GraphState) -> Dict[str, Any]:
    """
    Phase 4: Real-time analysis of user response for instant adaptation
    """
    current_question = state.get("current_question", {})
    conversation_history = state.get("conversation_history", [])
    
    # Build context for live analysis
    question_context = current_question.get("text", "") if current_question else ""
    conversation_summary = format_conversation_for_analysis(conversation_history)
    
    try:
        system_prompt = """
You are an expert learning analytics AI that analyzes student responses in real-time to optimize learning experiences.

Your task is to analyze a student's response and provide comprehensive insights for adaptive learning.

ANALYSIS FRAMEWORK:

🧠 UNDERSTANDING ASSESSMENT (0.0-1.0):
- 0.0-0.3: Minimal understanding, significant confusion
- 0.4-0.6: Developing understanding, some gaps
- 0.7-0.9: Good understanding, minor gaps
- 0.9-1.0: Excellent understanding, clear mastery

🎯 CONFIDENCE DETECTION (0.0-1.0):
- Language patterns indicating certainty vs uncertainty
- Hedging words, qualifiers, confidence markers
- Response completeness and detail level

📈 ENGAGEMENT MEASUREMENT (0.0-1.0):
- Enthusiasm, curiosity, active participation
- Question asking, elaboration, interest signals
- Response length and depth

🚨 CONFUSION INDICATORS:
- Specific phrases or patterns indicating confusion
- Misconceptions or errors in reasoning
- Requests for clarification or help

🎨 LEARNING STYLE SIGNALS:
- Visual preference indicators
- Verbal/auditory preference indicators  
- Experiential/hands-on preference indicators
- Step-by-step/systematic preference indicators

⚡ COGNITIVE LOAD ASSESSMENT:
- "low": Student handling information easily
- "moderate": Appropriate challenge level
- "high": Student may be overwhelmed

🔧 ADAPTATION RECOMMENDATIONS:
- difficulty_adjustment: "increase"|"decrease"|"maintain"
- teaching_strategy: "more_examples"|"deeper_explanation"|"practice_problems"|"conceptual_focus"
- conversation_style: "supportive"|"challenging"|"exploratory"|"direct"

Return comprehensive JSON analysis:

{
    "understanding": 0.75,
    "confidence": 0.65,
    "engagement": 0.80,
    "confusion_indicators": ["specific phrases indicating confusion"],
    "learning_style_signals": {
        "visual_preference": 0.3,
        "verbal_preference": 0.7,
        "experiential_preference": 0.4,
        "step_by_step_preference": 0.6
    },
    "cognitive_load": "moderate",
    "adaptation_recommendations": {
        "difficulty_adjustment": "maintain",
        "teaching_strategy": "more_examples",
        "conversation_style": "supportive"
    },
    "key_insights": [
        "Student shows good conceptual understanding",
        "Could benefit from more concrete examples"
    ],
    "response_quality_score": 0.73
}
"""

        user_prompt = f"""
CURRENT QUESTION CONTEXT:
{question_context}

CONVERSATION HISTORY:
{conversation_summary}

STUDENT'S LATEST RESPONSE:
"{user_input}"

RESPONSE LENGTH: {len(user_input)} characters

Analyze this response now and provide comprehensive insights.
"""

        analysis = call_ai_with_json_output(system_prompt, user_prompt)
        
        # Validate and ensure all fields are present
        analysis.setdefault("understanding", 0.5)
        analysis.setdefault("confidence", 0.5)
        analysis.setdefault("engagement", 0.5)
        analysis.setdefault("confusion_indicators", [])
        analysis.setdefault("learning_style_signals", {})
        analysis.setdefault("cognitive_load", "moderate")
        analysis.setdefault("adaptation_recommendations", {})
        analysis.setdefault("key_insights", [])
        analysis.setdefault("response_quality_score", 0.5)
        
        # Add timestamp and metadata
        analysis["timestamp"] = datetime.now(timezone.utc).isoformat()
        analysis["response_length"] = len(user_input)
        analysis["question_id"] = current_question.get("id", "unknown") if current_question else "unknown"
        
        logger.info(f"Live analysis complete: understanding={analysis['understanding']:.2f}, engagement={analysis['engagement']:.2f}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in live response analysis: {e}")
        return get_fallback_analysis(user_input)


def get_fallback_analysis(user_input: str) -> Dict[str, Any]:
    """Fallback analysis when AI analysis fails"""
    response_length = len(user_input)
    
    # Simple heuristic analysis
    understanding = min(0.8, response_length / 200)  # Longer responses suggest better understanding
    confidence = 0.6 if "I think" in user_input or "maybe" in user_input else 0.7
    engagement = min(0.9, response_length / 150)
    
    return {
        "understanding": understanding,
        "confidence": confidence,
        "engagement": engagement,
        "confusion_indicators": [],
        "learning_style_signals": {},
        "cognitive_load": "moderate",
        "adaptation_recommendations": {
            "difficulty_adjustment": "maintain",
            "teaching_strategy": "continue_current",
            "conversation_style": "supportive"
        },
        "key_insights": ["Analysis generated using fallback heuristics"],
        "response_quality_score": (understanding + confidence + engagement) / 3,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response_length": response_length,
        "fallback_analysis": True
    }


# ================================================================================================
# ADAPTIVE DIFFICULTY ENGINE
# ================================================================================================

def calculate_adaptive_difficulty(current_performance: Dict[str, float], 
                                historical_data: List[Dict], 
                                user_profile: Dict[str, Any]) -> float:
    """
    Phase 4: Calculate optimal difficulty level based on real-time performance
    """
    try:
        understanding = current_performance.get("understanding", 0.5)
        confidence = current_performance.get("confidence", 0.5)
        engagement = current_performance.get("engagement", 0.5)
        
        # Base difficulty from current performance
        base_difficulty = 1.0 - ((understanding + confidence) / 2)
        
        # Adjust based on engagement (high engagement = can handle more challenge)
        engagement_factor = 0.1 * (engagement - 0.5)  # -0.05 to +0.05
        
        # Historical performance trend
        historical_factor = 0.0
        if len(historical_data) >= 2:
            recent_scores = [item.get("performance_score", 0.5) for item in historical_data[-3:]]
            if len(recent_scores) >= 2:
                trend = recent_scores[-1] - recent_scores[0]
                historical_factor = trend * 0.1  # Small adjustment based on trend
        
        # User preference for challenge level
        challenge_preference = user_profile.get("challenge_preference", 0.5)
        preference_factor = (challenge_preference - 0.5) * 0.1
        
        # Calculate final difficulty
        final_difficulty = base_difficulty + engagement_factor + historical_factor + preference_factor
        
        # Clamp between 0.1 and 1.0
        return max(0.1, min(1.0, final_difficulty))
        
    except Exception as e:
        logger.error(f"Error calculating adaptive difficulty: {e}")
        return 0.5  # Safe default


def detect_learning_style(conversation_data: List[Dict], live_analysis: Dict[str, Any]) -> str:
    """
    Detect user's preferred learning style from conversation patterns
    """
    try:
        style_signals = live_analysis.get("learning_style_signals", {})
        
        visual_score = style_signals.get("visual_preference", 0.0)
        verbal_score = style_signals.get("verbal_preference", 0.0)
        experiential_score = style_signals.get("experiential_preference", 0.0)
        step_by_step_score = style_signals.get("step_by_step_preference", 0.0)
        
        # Find dominant style
        scores = {
            "visual": visual_score,
            "verbal": verbal_score,
            "experiential": experiential_score,
            "systematic": step_by_step_score
        }
        
        dominant_style = max(scores, key=scores.get)
        
        # Only return if confidence is high enough
        if scores[dominant_style] > 0.6:
            return dominant_style
        else:
            return "balanced"
            
    except Exception as e:
        logger.error(f"Error detecting learning style: {e}")
        return "balanced"


async def determine_adaptive_conversation_strategy(understanding_level: float,
                                                 engagement_level: float,
                                                 confusion_signals: List[str],
                                                 user_preferences: Dict[str, Any],
                                                 conversation_history: List[Dict]) -> Dict[str, Any]:
    """
    Determine optimal conversation strategy based on current state
    """
    try:
        # Base strategy from understanding and engagement
        if understanding_level < 0.4:
            base_strategy = "supportive_explanation"
        elif understanding_level > 0.8 and engagement_level > 0.7:
            base_strategy = "challenge_extension"
        elif engagement_level < 0.4:
            base_strategy = "engagement_boost"
        else:
            base_strategy = "progressive_questioning"
        
        # Adjust for confusion signals
        strategy_adjustments = []
        if confusion_signals:
            strategy_adjustments.append("clarification_focus")
        
        # Consider user preferences
        learning_style = user_preferences.get("learning_style", "balanced")
        if learning_style == "visual":
            strategy_adjustments.append("encourage_visualization")
        elif learning_style == "experiential":
            strategy_adjustments.append("practical_examples")
        
        return {
            "primary_strategy": base_strategy,
            "adjustments": strategy_adjustments,
            "confidence_level": min(understanding_level + engagement_level, 1.0),
            "recommendation": f"Use {base_strategy} with {', '.join(strategy_adjustments) if strategy_adjustments else 'no special adjustments'}"
        }
        
    except Exception as e:
        logger.error(f"Error determining conversation strategy: {e}")
        return get_fallback_strategy(understanding_level, engagement_level)


def get_fallback_strategy(understanding_level: float, engagement_level: float) -> Dict[str, Any]:
    """Fallback strategy when AI analysis fails"""
    if understanding_level < 0.5:
        strategy = "supportive_explanation"
    elif engagement_level < 0.5:
        strategy = "engagement_boost"
    else:
        strategy = "progressive_questioning"
    
    return {
        "primary_strategy": strategy,
        "adjustments": [],
        "confidence_level": 0.5,
        "recommendation": f"Fallback strategy: {strategy}",
        "fallback": True
    }


def update_live_performance_metrics(state: GraphState, live_analysis: Dict[str, Any]) -> None:
    """
    Update state with live performance metrics
    """
    try:
        # Initialize performance tracking if not exists
        if "live_performance_metrics" not in state:
            state["live_performance_metrics"] = []
        
        # Add current analysis to metrics
        metrics_entry = {
            "timestamp": live_analysis.get("timestamp"),
            "understanding": live_analysis.get("understanding", 0.5),
            "confidence": live_analysis.get("confidence", 0.5),
            "engagement": live_analysis.get("engagement", 0.5),
            "response_quality": live_analysis.get("response_quality_score", 0.5),
            "cognitive_load": live_analysis.get("cognitive_load", "moderate")
        }
        
        state["live_performance_metrics"].append(metrics_entry)
        
        # Keep only last 20 entries to avoid memory bloat
        if len(state["live_performance_metrics"]) > 20:
            state["live_performance_metrics"] = state["live_performance_metrics"][-20:]
        
        # Update rolling averages
        recent_metrics = state["live_performance_metrics"][-5:]  # Last 5 responses
        
        state["current_performance_average"] = {
            "understanding": mean([m["understanding"] for m in recent_metrics]),
            "confidence": mean([m["confidence"] for m in recent_metrics]),
            "engagement": mean([m["engagement"] for m in recent_metrics]),
            "response_quality": mean([m["response_quality"] for m in recent_metrics])
        }
        
        logger.info(f"Updated live performance metrics: {len(state['live_performance_metrics'])} entries")
        
    except Exception as e:
        logger.error(f"Error updating live performance metrics: {e}")


def update_learned_preferences(state: GraphState, live_analysis: Dict[str, Any]) -> None:
    """
    Update learned user preferences based on response patterns
    """
    try:
        if "learned_preferences" not in state:
            state["learned_preferences"] = {
                "learning_style_scores": {"visual": 0.0, "verbal": 0.0, "experiential": 0.0, "systematic": 0.0},
                "challenge_preference": 0.5,
                "interaction_style": "balanced",
                "feedback_preference": "detailed"
            }
        
        # Update learning style signals
        style_signals = live_analysis.get("learning_style_signals", {})
        for style, score in style_signals.items():
            if style.endswith("_preference"):
                style_key = style.replace("_preference", "")
                if style_key in state["learned_preferences"]["learning_style_scores"]:
                    # Use exponential moving average to update preferences
                    current = state["learned_preferences"]["learning_style_scores"][style_key]
                    state["learned_preferences"]["learning_style_scores"][style_key] = current * 0.8 + score * 0.2
        
        # Update challenge preference based on engagement with difficulty
        engagement = live_analysis.get("engagement", 0.5)
        cognitive_load = live_analysis.get("cognitive_load", "moderate")
        
        if cognitive_load == "high" and engagement > 0.7:
            # High challenge and high engagement = likes challenge
            state["learned_preferences"]["challenge_preference"] = min(1.0, state["learned_preferences"]["challenge_preference"] + 0.05)
        elif cognitive_load == "low" and engagement < 0.5:
            # Low challenge and low engagement = needs more challenge
            state["learned_preferences"]["challenge_preference"] = min(1.0, state["learned_preferences"]["challenge_preference"] + 0.03)
        elif cognitive_load == "high" and engagement < 0.4:
            # High challenge and low engagement = too much challenge
            state["learned_preferences"]["challenge_preference"] = max(0.0, state["learned_preferences"]["challenge_preference"] - 0.05)
        
        logger.info("Updated learned preferences based on response analysis")
        
    except Exception as e:
        logger.error(f"Error updating learned preferences: {e}")


def format_conversation_for_analysis(conversation_history: List[Dict]) -> str:
    """Format conversation history for AI analysis"""
    if not conversation_history:
        return "No conversation history available."
    
    # Take last 6 messages for context
    recent_history = conversation_history[-6:]
    
    formatted = []
    for msg in recent_history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        formatted.append(f"{role.title()}: {content}")
    
    return "\n".join(formatted)


def calculate_learning_momentum(state: GraphState) -> float:
    """Calculate learning momentum based on recent performance"""
    try:
        metrics = state.get("live_performance_metrics", [])
        if len(metrics) < 3:
            return 0.5  # Neutral momentum
        
        # Get recent performance scores
        recent_scores = [m["response_quality"] for m in metrics[-5:]]
        
        # Calculate trend
        if len(recent_scores) >= 2:
            trend = recent_scores[-1] - recent_scores[0]
            momentum = 0.5 + (trend * 0.5)  # Convert trend to momentum score
            return max(0.0, min(1.0, momentum))
        
        return 0.5
        
    except Exception as e:
        logger.error(f"Error calculating learning momentum: {e}")
        return 0.5


def log_adaptation_decision(state: GraphState, decision_data: Dict[str, Any]) -> None:
    """Log adaptation decisions for analysis"""
    try:
        if "adaptation_log" not in state:
            state["adaptation_log"] = []
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision_type": decision_data.get("type", "unknown"),
            "decision_data": decision_data,
            "state_snapshot": {
                "current_performance": state.get("current_performance_average", {}),
                "learning_momentum": calculate_learning_momentum(state)
            }
        }
        
        state["adaptation_log"].append(log_entry)
        
        # Keep only last 50 entries
        if len(state["adaptation_log"]) > 50:
            state["adaptation_log"] = state["adaptation_log"][-50:]
        
        logger.info(f"Logged adaptation decision: {decision_data.get('type', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Error logging adaptation decision: {e}") 