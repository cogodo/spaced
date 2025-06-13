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

from my_agent.utils.tools import call_ai_with_json_output, call_ai_for_simple_response
from my_agent.utils.state import GraphState

logger = logging.getLogger(__name__)

# ================================================================================================
# REAL-TIME ANALYSIS ENGINE
# ================================================================================================

async def analyze_user_response_live(user_input: str, state: GraphState) -> Dict[str, Any]:
    """
    Phase 4: Real-time analysis of user response for instant adaptation
    """
    current_question = state.get("current_question", {})
    conversation_history = current_question.get("conversation_history", [])
    
    # Build context for live analysis
    question_context = current_question.get("text", "")
    conversation_summary = format_conversation_for_analysis(conversation_history)
    
    analysis_prompt = f"""
You are an expert learning analytics AI performing real-time analysis of a student's response for instant adaptation.

USER RESPONSE: "{user_input}"
QUESTION CONTEXT: "{question_context}"
CONVERSATION HISTORY: {conversation_summary}

Provide instant analysis for real-time learning adaptation:

🧠 UNDERSTANDING LEVEL (0.0-1.0):
Analyze conceptual grasp, accuracy, and depth of explanation.

🎯 CONFIDENCE SIGNALS (0.0-1.0): 
Detect language certainty, hedging vs definitive statements, clarification requests.

⚡ ENGAGEMENT LEVEL (0.0-1.0):
Evaluate response enthusiasm, detail level, and question-asking behavior.

🚨 CONFUSION INDICATORS:
Identify misconceptions, understanding gaps, and clarification needs.

🎨 LEARNING STYLE SIGNALS:
Detect visual descriptions, step-by-step thinking, examples, abstract vs concrete preferences.

💭 COGNITIVE LOAD ASSESSMENT:
Evaluate complexity handling, processing speed, and scaffolding needs.

🚀 ADAPTATION RECOMMENDATIONS:
Suggest immediate conversation adjustments for optimal learning.

Return JSON:
{{
    "understanding": 0.85,
    "confidence": 0.75,
    "engagement": 0.90,
    "confusion_indicators": ["specific misconception", "knowledge gap"],
    "learning_style_signals": {{
        "visual_preference": 0.3,
        "verbal_preference": 0.8,
        "experiential_preference": 0.6,
        "step_by_step_preference": 0.7
    }},
    "cognitive_load": "moderate",
    "processing_speed": "fast",
    "adaptation_recommendations": {{
        "difficulty_adjustment": "maintain",
        "teaching_strategy": "elaborative_questioning",
        "conversation_style": "encouragement_focused",
        "next_question_type": "application"
    }},
    "key_insights": ["insight 1", "insight 2"],
    "response_quality_score": 0.82
}}
"""

    try:
        analysis = call_ai_with_json_output(analysis_prompt)
        
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
        analysis["question_id"] = current_question.get("id", "unknown")
        
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
            if len(recent_scores) > 1:
                trend = recent_scores[-1] - recent_scores[0]
                historical_factor = -0.1 * trend  # Improving = lower difficulty
        
        # User profile adjustments
        profile_factor = 0.0
        learning_style = user_profile.get("detected_learning_style", "mixed")
        if learning_style == "visual" and current_performance.get("visual_preference", 0) > 0.7:
            profile_factor -= 0.05  # Slightly easier for strong visual learners
        elif learning_style == "experiential" and current_performance.get("experiential_preference", 0) > 0.7:
            profile_factor += 0.05  # Slightly harder for experiential learners
        
        # Combine factors
        adaptive_difficulty = base_difficulty + engagement_factor + historical_factor + profile_factor
        
        # Clamp to valid range with smoothing
        adaptive_difficulty = max(0.1, min(0.9, adaptive_difficulty))
        
        logger.info(f"Adaptive difficulty calculated: {adaptive_difficulty:.3f} (base: {base_difficulty:.3f})")
        
        return adaptive_difficulty
        
    except Exception as e:
        logger.error(f"Error calculating adaptive difficulty: {e}")
        return 0.5  # Default to medium difficulty


# ================================================================================================
# LEARNING STYLE DETECTION
# ================================================================================================

def detect_learning_style(conversation_data: List[Dict], live_analysis: Dict[str, Any]) -> str:
    """
    Phase 4: Detect user's learning style from conversation patterns
    """
    try:
        style_signals = live_analysis.get("learning_style_signals", {})
        
        # Accumulate signals from conversation history
        visual_signals = style_signals.get("visual_preference", 0)
        verbal_signals = style_signals.get("verbal_preference", 0)
        experiential_signals = style_signals.get("experiential_preference", 0)
        kinesthetic_signals = style_signals.get("step_by_step_preference", 0)
        
        # Analyze conversation history for style patterns
        for message in conversation_data:
            content = message.get("content", "").lower()
            
            # Visual learner indicators
            if any(word in content for word in ["picture", "visualize", "see", "image", "diagram", "chart"]):
                visual_signals += 0.1
            
            # Verbal learner indicators  
            if any(word in content for word in ["explain", "tell me", "describe", "say", "words"]):
                verbal_signals += 0.1
            
            # Experiential learner indicators
            if any(word in content for word in ["example", "real-world", "practice", "try", "experience", "hands-on"]):
                experiential_signals += 0.1
            
            # Kinesthetic/step-by-step indicators
            if any(word in content for word in ["step", "process", "sequence", "order", "procedure"]):
                kinesthetic_signals += 0.1
        
        # Determine dominant style
        style_scores = {
            "visual": visual_signals,
            "verbal": verbal_signals,
            "experiential": experiential_signals,
            "kinesthetic": kinesthetic_signals
        }
        
        dominant_style = max(style_scores, key=style_scores.get)
        max_score = style_scores[dominant_style]
        
        # Require minimum threshold for confident detection
        if max_score < 0.3:
            return "mixed"
        
        # Check for close competition (mixed style)
        sorted_scores = sorted(style_scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] - sorted_scores[1] < 0.15:
            return "mixed"
        
        logger.info(f"Learning style detected: {dominant_style} (score: {max_score:.2f})")
        
        return dominant_style
        
    except Exception as e:
        logger.error(f"Error detecting learning style: {e}")
        return "mixed"


# ================================================================================================
# CONVERSATION STRATEGY ADAPTATION
# ================================================================================================

async def determine_adaptive_conversation_strategy(understanding_level: float,
                                                 engagement_level: float,
                                                 confusion_signals: List[str],
                                                 user_preferences: Dict[str, Any],
                                                 conversation_history: List[Dict]) -> Dict[str, Any]:
    """
    Phase 4: Determine optimal conversation strategy based on live analysis
    """
    try:
        # Analyze current conversation context
        conversation_length = len(conversation_history)
        learning_style = user_preferences.get("detected_learning_style", "mixed")
        cognitive_load = user_preferences.get("cognitive_load_level", "moderate")
        
        strategy_prompt = f"""
Design the optimal conversation strategy for real-time adaptation:

LIVE ANALYSIS:
- Understanding Level: {understanding_level:.2f}/1.0
- Engagement Level: {engagement_level:.2f}/1.0
- Confusion Signals: {confusion_signals}
- Learning Style: {learning_style}
- Cognitive Load: {cognitive_load}
- Conversation Length: {conversation_length} exchanges

USER PREFERENCES:
{json.dumps(user_preferences, indent=2)}

Select optimal teaching approach:

📚 TEACHING STRATEGIES:
- socratic_questioning: Guide discovery through questions
- direct_instruction: Provide clear information and explanations
- scaffolded_learning: Step-by-step support and building
- elaborative_interrogation: Deep why/how questions
- analogical_reasoning: Use comparisons and examples

🎯 DIFFICULTY ADJUSTMENTS:
- increase_challenge: User is ready for more complexity
- provide_support: User needs more scaffolding
- maintain_current: Current level is optimal

🗣️ CONVERSATION STYLE:
- tone: formal/conversational/encouraging/challenging
- pacing: fast/moderate/slow
- question_density: high/medium/low
- language_level: technical/accessible/simplified

⚡ ENGAGEMENT TACTICS:
- curiosity_questions: Spark interest and wonder
- real_world_applications: Connect to practical uses
- interactive_examples: Hands-on demonstrations
- personal_relevance: Connect to user's interests

Return JSON strategy:
{{
    "teaching_strategy": "socratic_questioning",
    "difficulty_adjustment": "maintain_current",
    "conversation_style": {{
        "tone": "encouraging",
        "pacing": "moderate",
        "question_density": "medium",
        "language_level": "accessible"
    }},
    "engagement_tactics": ["curiosity_questions", "real_world_applications"],
    "personalization_applied": ["learning_style_adaptation", "cognitive_load_consideration"],
    "adaptation_reasoning": "User shows good understanding but could use more engagement",
    "confidence_score": 0.85
}}
"""

        strategy = call_ai_with_json_output(strategy_prompt)
        
        # Validate and provide defaults
        strategy.setdefault("teaching_strategy", "socratic_questioning")
        strategy.setdefault("difficulty_adjustment", "maintain_current")
        strategy.setdefault("conversation_style", {
            "tone": "encouraging",
            "pacing": "moderate", 
            "question_density": "medium",
            "language_level": "accessible"
        })
        strategy.setdefault("engagement_tactics", ["curiosity_questions"])
        strategy.setdefault("personalization_applied", [])
        strategy.setdefault("adaptation_reasoning", "Adaptive strategy based on current performance")
        strategy.setdefault("confidence_score", 0.7)
        
        # Add metadata
        strategy["timestamp"] = datetime.now(timezone.utc).isoformat()
        strategy["context"] = {
            "understanding": understanding_level,
            "engagement": engagement_level,
            "confusion_count": len(confusion_signals)
        }
        
        logger.info(f"Adaptive strategy determined: {strategy['teaching_strategy']} with {strategy['difficulty_adjustment']}")
        
        return strategy
        
    except Exception as e:
        logger.error(f"Error determining conversation strategy: {e}")
        return get_fallback_strategy(understanding_level, engagement_level)


def get_fallback_strategy(understanding_level: float, engagement_level: float) -> Dict[str, Any]:
    """Fallback strategy when AI strategy fails"""
    
    # Simple heuristic strategy selection
    if understanding_level < 0.4:
        teaching_strategy = "scaffolded_learning"
        difficulty_adjustment = "provide_support"
    elif understanding_level > 0.8:
        teaching_strategy = "elaborative_interrogation"
        difficulty_adjustment = "increase_challenge"
    else:
        teaching_strategy = "socratic_questioning"
        difficulty_adjustment = "maintain_current"
    
    # Engagement-based conversation style
    if engagement_level < 0.4:
        tone = "encouraging"
        engagement_tactics = ["curiosity_questions", "personal_relevance"]
    elif engagement_level > 0.8:
        tone = "challenging"
        engagement_tactics = ["real_world_applications"]
    else:
        tone = "conversational"
        engagement_tactics = ["interactive_examples"]
    
    return {
        "teaching_strategy": teaching_strategy,
        "difficulty_adjustment": difficulty_adjustment,
        "conversation_style": {
            "tone": tone,
            "pacing": "moderate",
            "question_density": "medium",
            "language_level": "accessible"
        },
        "engagement_tactics": engagement_tactics,
        "personalization_applied": ["heuristic_adaptation"],
        "adaptation_reasoning": "Fallback strategy based on understanding and engagement levels",
        "confidence_score": 0.6,
        "fallback_strategy": True
    }


# ================================================================================================
# LIVE PERFORMANCE TRACKING
# ================================================================================================

def update_live_performance_metrics(state: GraphState, live_analysis: Dict[str, Any]) -> None:
    """
    Phase 4: Update live performance metrics in state
    """
    try:
        # Initialize if not present
        if "live_performance_metrics" not in state:
            state["live_performance_metrics"] = {
                "understanding_history": [],
                "confidence_history": [],
                "engagement_history": [],
                "current_understanding": 0.5,
                "current_confidence": 0.5,
                "current_engagement": 0.5,
                "performance_trend": "stable",
                "session_average": 0.5
            }
        
        metrics = state["live_performance_metrics"]
        
        # Update current metrics
        metrics["current_understanding"] = live_analysis.get("understanding", 0.5)
        metrics["current_confidence"] = live_analysis.get("confidence", 0.5)
        metrics["current_engagement"] = live_analysis.get("engagement", 0.5)
        
        # Update history
        metrics["understanding_history"].append(metrics["current_understanding"])
        metrics["confidence_history"].append(metrics["current_confidence"])
        metrics["engagement_history"].append(metrics["current_engagement"])
        
        # Keep only recent history (last 10 responses)
        for key in ["understanding_history", "confidence_history", "engagement_history"]:
            if len(metrics[key]) > 10:
                metrics[key] = metrics[key][-10:]
        
        # Calculate session average
        all_scores = (metrics["understanding_history"] + 
                     metrics["confidence_history"] + 
                     metrics["engagement_history"])
        metrics["session_average"] = mean(all_scores) if all_scores else 0.5
        
        # Determine performance trend
        if len(metrics["understanding_history"]) >= 3:
            recent_avg = mean(metrics["understanding_history"][-3:])
            earlier_avg = mean(metrics["understanding_history"][-6:-3]) if len(metrics["understanding_history"]) >= 6 else metrics["understanding_history"][0]
            
            if recent_avg > earlier_avg + 0.1:
                metrics["performance_trend"] = "improving"
            elif recent_avg < earlier_avg - 0.1:
                metrics["performance_trend"] = "declining"
            else:
                metrics["performance_trend"] = "stable"
        
        # Add timestamp
        metrics["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        logger.debug(f"Live metrics updated: understanding={metrics['current_understanding']:.2f}, trend={metrics['performance_trend']}")
        
    except Exception as e:
        logger.error(f"Error updating live performance metrics: {e}")


def update_learned_preferences(state: GraphState, live_analysis: Dict[str, Any]) -> None:
    """
    Phase 4: Update learned user preferences from live analysis
    """
    try:
        # Initialize if not present
        if "learned_user_preferences" not in state:
            state["learned_user_preferences"] = {
                "learning_style_signals": {},
                "communication_preferences": {},
                "cognitive_patterns": {},
                "motivation_factors": {},
                "discovery_count": 0
            }
        
        preferences = state["learned_user_preferences"]
        preferences["discovery_count"] += 1
        
        # Update learning style signals
        style_signals = live_analysis.get("learning_style_signals", {})
        for style, score in style_signals.items():
            if style not in preferences["learning_style_signals"]:
                preferences["learning_style_signals"][style] = []
            preferences["learning_style_signals"][style].append(score)
            
            # Keep only recent signals
            if len(preferences["learning_style_signals"][style]) > 10:
                preferences["learning_style_signals"][style] = preferences["learning_style_signals"][style][-10:]
        
        # Update cognitive patterns
        cognitive_load = live_analysis.get("cognitive_load", "moderate")
        if "cognitive_load_history" not in preferences["cognitive_patterns"]:
            preferences["cognitive_patterns"]["cognitive_load_history"] = []
        preferences["cognitive_patterns"]["cognitive_load_history"].append(cognitive_load)
        
        # Detect learning style
        conversation_history = state.get("adaptive_conversation_history", [])
        detected_style = detect_learning_style(conversation_history, live_analysis)
        if detected_style != "mixed":
            state["detected_learning_style"] = detected_style
        
        # Update engagement trend
        engagement_level = live_analysis.get("engagement", 0.5)
        if "engagement_trend_history" not in preferences:
            preferences["engagement_trend_history"] = []
        preferences["engagement_trend_history"].append(engagement_level)
        
        # Determine engagement trend
        if len(preferences["engagement_trend_history"]) >= 3:
            recent_trend = preferences["engagement_trend_history"][-3:]
            if all(recent_trend[i] >= recent_trend[i-1] for i in range(1, len(recent_trend))):
                state["engagement_trend"] = "increasing"
            elif all(recent_trend[i] <= recent_trend[i-1] for i in range(1, len(recent_trend))):
                state["engagement_trend"] = "declining"  
            else:
                state["engagement_trend"] = "stable"
        
        preferences["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        logger.debug(f"Learned preferences updated: style={state.get('detected_learning_style', 'unknown')}, trend={state.get('engagement_trend', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Error updating learned preferences: {e}")


# ================================================================================================
# UTILITY FUNCTIONS
# ================================================================================================

def format_conversation_for_analysis(conversation_history: List[Dict]) -> str:
    """Format conversation history for AI analysis"""
    if not conversation_history:
        return "No conversation history available"
    
    # Get last 3 exchanges for context
    recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
    
    formatted = []
    for msg in recent_history:
        role = "AI" if msg.get("role") == "assistant" else "User"
        content = msg.get("content", "")[:150] + "..." if len(msg.get("content", "")) > 150 else msg.get("content", "")
        formatted.append(f"{role}: {content}")
    
    return "\n".join(formatted)


def calculate_learning_momentum(state: GraphState) -> float:
    """Calculate current learning momentum score"""
    try:
        live_metrics = state.get("live_performance_metrics", {})
        understanding_history = live_metrics.get("understanding_history", [])
        
        if len(understanding_history) < 2:
            return 0.5
        
        # Calculate momentum from recent performance
        recent_scores = understanding_history[-3:] if len(understanding_history) >= 3 else understanding_history
        
        if len(recent_scores) == 1:
            return recent_scores[0]
        
        # Calculate improvement rate
        improvement = recent_scores[-1] - recent_scores[0]
        momentum = 0.5 + (improvement * 0.5)  # Scale to 0-1
        
        # Factor in consistency
        if len(recent_scores) >= 3:
            consistency = 1.0 - (stdev(recent_scores) if len(recent_scores) > 1 else 0)
            momentum = momentum * 0.8 + consistency * 0.2
        
        return max(0.0, min(1.0, momentum))
        
    except Exception as e:
        logger.error(f"Error calculating learning momentum: {e}")
        return 0.5


def log_adaptation_decision(state: GraphState, question: Dict[str, Any], difficulty: float) -> None:
    """Log adaptation decisions for analytics"""
    try:
        if "session_optimization_log" not in state:
            state["session_optimization_log"] = []
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "adaptation_type": "question_selection",
            "question_id": question.get("id", "unknown"),
            "adapted_difficulty": difficulty,
            "reasoning": f"Difficulty adapted to {difficulty:.2f} based on live performance",
            "performance_context": state.get("live_performance_metrics", {}).get("current_understanding", 0.5)
        }
        
        state["session_optimization_log"].append(log_entry)
        
        # Keep log size manageable
        if len(state["session_optimization_log"]) > 50:
            state["session_optimization_log"] = state["session_optimization_log"][-50:]
            
    except Exception as e:
        logger.error(f"Error logging adaptation decision: {e}") 