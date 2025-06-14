"""
Adaptive State Integration Module
Handles integration of adaptive learning features with the graph state
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from agent.state import GraphState

logger = logging.getLogger(__name__)

def auto_restore_adaptive_state(state: GraphState) -> None:
    """
    Restore adaptive state from previous sessions or initialize if new
    """
    try:
        # Initialize adaptive state if not present
        if "adaptive_state" not in state:
            state["adaptive_state"] = {
                "initialized": True,
                "initialization_time": datetime.now(timezone.utc).isoformat(),
                "learning_profile": {
                    "preferred_difficulty": 0.5,
                    "learning_style": "balanced",
                    "engagement_patterns": {},
                    "performance_history": []
                },
                "session_adaptations": [],
                "cumulative_metrics": {
                    "total_responses": 0,
                    "avg_understanding": 0.5,
                    "avg_engagement": 0.5,
                    "learning_velocity": 0.5
                }
            }
            logger.info("Initialized new adaptive state")
        else:
            logger.info("Restored existing adaptive state")
            
    except Exception as e:
        logger.error(f"Error in auto_restore_adaptive_state: {e}")


def auto_save_adaptive_state(state: GraphState) -> bool:
    """
    Save current adaptive state for future sessions
    """
    try:
        # Update cumulative metrics
        if "adaptive_state" in state and "live_performance_metrics" in state:
            metrics = state["live_performance_metrics"]
            if metrics:
                # Update cumulative metrics
                cumulative = state["adaptive_state"]["cumulative_metrics"]
                cumulative["total_responses"] = len(metrics)
                
                # Calculate averages
                if metrics:
                    cumulative["avg_understanding"] = sum(m.get("understanding", 0.5) for m in metrics) / len(metrics)
                    cumulative["avg_engagement"] = sum(m.get("engagement", 0.5) for m in metrics) / len(metrics)
                
                # Update last save time
                state["adaptive_state"]["last_saved"] = datetime.now(timezone.utc).isoformat()
        
        logger.info("Adaptive state saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error saving adaptive state: {e}")
        return False


def log_adaptive_decision(state: GraphState, decision_type: str, decision_data: Dict[str, Any]) -> None:
    """
    Log adaptive decisions for analysis and debugging
    """
    try:
        if "adaptive_state" not in state:
            auto_restore_adaptive_state(state)
        
        # Add decision to session adaptations
        decision_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": decision_type,
            "data": decision_data,
            "session_context": {
                "message_count": state.get("message_count", 0),
                "current_topic": state.get("topics", [{}])[state.get("current_topic_index", 0)] if state.get("topics") else None
            }
        }
        
        state["adaptive_state"]["session_adaptations"].append(decision_entry)
        
        # Keep only last 50 decisions to avoid memory bloat
        if len(state["adaptive_state"]["session_adaptations"]) > 50:
            state["adaptive_state"]["session_adaptations"] = state["adaptive_state"]["session_adaptations"][-50:]
        
        logger.info(f"Logged adaptive decision: {decision_type}")
        
    except Exception as e:
        logger.error(f"Error logging adaptive decision: {e}")


def update_learning_profile(state: GraphState, performance_data: Dict[str, Any]) -> None:
    """
    Update the user's learning profile based on performance data
    """
    try:
        if "adaptive_state" not in state:
            auto_restore_adaptive_state(state)
        
        profile = state["adaptive_state"]["learning_profile"]
        
        # Update preferred difficulty based on performance and engagement
        understanding = performance_data.get("understanding", 0.5)
        engagement = performance_data.get("engagement", 0.5)
        cognitive_load = performance_data.get("cognitive_load", "moderate")
        
        # Adjust preferred difficulty
        if cognitive_load == "high" and engagement > 0.7:
            # High challenge with high engagement = increase difficulty preference
            profile["preferred_difficulty"] = min(1.0, profile["preferred_difficulty"] + 0.02)
        elif cognitive_load == "low" and engagement < 0.5:
            # Low challenge with low engagement = increase difficulty preference
            profile["preferred_difficulty"] = min(1.0, profile["preferred_difficulty"] + 0.01)
        elif cognitive_load == "high" and engagement < 0.4:
            # High challenge with low engagement = decrease difficulty preference
            profile["preferred_difficulty"] = max(0.0, profile["preferred_difficulty"] - 0.02)
        
        # Update learning style based on style signals
        style_signals = performance_data.get("learning_style_signals", {})
        if style_signals:
            # Simple heuristic to update learning style
            max_signal = max(style_signals.items(), key=lambda x: x[1])
            if max_signal[1] > 0.7:  # Strong signal
                style_name = max_signal[0].replace("_preference", "")
                profile["learning_style"] = style_name
        
        # Add to performance history
        profile["performance_history"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "understanding": understanding,
            "engagement": engagement,
            "cognitive_load": cognitive_load
        })
        
        # Keep only last 20 performance entries
        if len(profile["performance_history"]) > 20:
            profile["performance_history"] = profile["performance_history"][-20:]
        
        logger.info("Updated learning profile")
        
    except Exception as e:
        logger.error(f"Error updating learning profile: {e}")


def get_adaptive_recommendations(state: GraphState) -> Dict[str, Any]:
    """
    Get adaptive recommendations based on current state
    """
    try:
        if "adaptive_state" not in state:
            return {"difficulty": 0.5, "strategy": "balanced", "confidence": 0.0}
        
        profile = state["adaptive_state"]["learning_profile"]
        recent_performance = state.get("current_performance_average", {})
        
        # Get difficulty recommendation
        preferred_difficulty = profile.get("preferred_difficulty", 0.5)
        current_understanding = recent_performance.get("understanding", 0.5)
        
        # Adjust difficulty based on recent performance
        if current_understanding > 0.8:
            recommended_difficulty = min(1.0, preferred_difficulty + 0.1)
        elif current_understanding < 0.4:
            recommended_difficulty = max(0.2, preferred_difficulty - 0.1)
        else:
            recommended_difficulty = preferred_difficulty
        
        # Get strategy recommendation
        learning_style = profile.get("learning_style", "balanced")
        engagement = recent_performance.get("engagement", 0.5)
        
        if engagement < 0.4:
            strategy = "engagement_boost"
        elif learning_style == "visual":
            strategy = "visual_explanations"
        elif learning_style == "experiential":
            strategy = "practical_examples"
        elif learning_style == "systematic":
            strategy = "step_by_step"
        else:
            strategy = "balanced"
        
        # Calculate confidence in recommendations
        performance_history = profile.get("performance_history", [])
        confidence = min(1.0, len(performance_history) / 10)  # More data = more confidence
        
        return {
            "difficulty": recommended_difficulty,
            "strategy": strategy,
            "learning_style": learning_style,
            "confidence": confidence,
            "reasoning": f"Based on {len(performance_history)} performance data points"
        }
        
    except Exception as e:
        logger.error(f"Error getting adaptive recommendations: {e}")
        return {"difficulty": 0.5, "strategy": "balanced", "confidence": 0.0}


def reset_session_adaptations(state: GraphState) -> None:
    """
    Reset session-specific adaptations while preserving learning profile
    """
    try:
        if "adaptive_state" in state:
            state["adaptive_state"]["session_adaptations"] = []
            state["adaptive_state"]["session_start"] = datetime.now(timezone.utc).isoformat()
            logger.info("Reset session adaptations")
        
    except Exception as e:
        logger.error(f"Error resetting session adaptations: {e}") 