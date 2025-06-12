from typing import Dict, Any
from datetime import datetime, timezone
from my_agent.utils.state import GraphState
from my_agent.utils.tools import call_main_llm, call_evaluator_llm, should_extend_session, should_complete_early

def respond_node(state: GraphState) -> Dict[str, Any]:
    """
    Enhanced respond node with Phase 5 adaptive features.
    
    Features:
    - Adaptive session length based on performance
    - Intelligent early completion
    - Advanced progress tracking
    - Cross-topic insights generation
    - Performance momentum analysis
    """
    # Pull config
    max_q = state["max_questions"]
    max_t = state["max_topics"]
    topics = state["topics"]
    session_type = state.get("session_type", "custom_topics")

    # If this is the first ever call (user_input == None), ask the first question
    if state["user_input"] is None:
        # Initialize counters and tracking
        state["current_topic_index"] = 0
        state["question_count"] = 1
        state["done"] = False
        state["history"] = []
        state["question_types"] = []  # Track question types for evaluation
        
        # Phase 5: Initialize advanced features
        state["session_start_time"] = datetime.now(timezone.utc).isoformat()
        state["adaptive_session_length"] = state.get("adaptive_session_length", True)  # Enable by default
        state["performance_threshold"] = state.get("performance_threshold", 4.5)
        state["struggle_threshold"] = state.get("struggle_threshold", 2.0)
        state["performance_trends"] = {}
        state["answer_confidence_scores"] = []
        state["question_difficulty_progression"] = []
        
        # Set current task for due_items sessions
        if session_type == "due_items" and topics:
            state["current_task"] = topics[0]
            state["progress"] = f"1/{len(topics)} tasks"
        
        # Ask the first question
        question = call_main_llm(state)
        state["next_question"] = question
        
        return {
            "next_question": question,
            "current_topic_index": state["current_topic_index"],
            "question_count": state["question_count"],
            "history": state["history"],
            "done": state["done"],
            "current_task": state.get("current_task"),
            "progress": state.get("progress"),
            "question_types": state.get("question_types", []),
            # Phase 5: Additional tracking
            "adaptive_mode": state.get("adaptive_session_length", False),
            "session_start_time": state.get("session_start_time")
        }

    # Otherwise, user_input is an answer to the *last* question we sent
    last_answer = state["user_input"]
    last_question = state.get("next_question", "")
    current_topic = topics[state["current_topic_index"]] if topics else "unknown"
    
    # Find the question type for this Q&A pair
    question_types = state.get("question_types", [])
    current_question_type = "cued_recall"  # Default fallback
    for qt in question_types:
        if qt.get("question") == last_question and qt.get("topic") == current_topic:
            current_question_type = qt.get("type", "cued_recall")
            break
    
    # Record that Q&A pair in history with topic and question type context
    state["history"].append({
        "question": last_question, 
        "answer": last_answer,
        "topic": current_topic,
        "question_type": current_question_type,
        "timestamp": datetime.now(timezone.utc).isoformat()  # Phase 5: Track timing
    })

    # Clear the user_input for the next run
    state["user_input"] = None

    # Phase 5: Check for adaptive session completion
    if should_complete_early(state):
        state["done"] = True
        state["session_completion_reason"] = "performance_achieved"
        state["session_end_time"] = datetime.now(timezone.utc).isoformat()
        state["next_question"] = None
        
        return {
            "done": True,
            "history": state["history"],
            "current_task": state.get("current_task"),
            "progress": "Early completion - excellent performance!",
            "question_types": state.get("question_types", []),
            "completion_reason": "performance_achieved",
            "adaptive_completion": True
        }

    # Check if we've hit the per-topic question limit
    if state["question_count"] < max_q:
        # Phase 5: Check if we should extend session for struggling performance
        if should_extend_session(state):
            # Extend the session by increasing max questions for this topic
            state["max_questions"] = min(state["max_questions"] + 2, 10)  # Max extension to 10
            print(f"🔄 Extending session for topic '{current_topic}' due to struggling performance")
        
        # Ask another question on the same topic
        state["question_count"] += 1
        question = call_main_llm(state)
        
        # Handle early completion signal from question generator
        if question is None:
            state["done"] = True
            state["session_end_time"] = datetime.now(timezone.utc).isoformat()
            state["next_question"] = None
            
            return {
                "done": True,
                "history": state["history"],
                "current_task": state.get("current_task"),
                "progress": "Early completion - performance threshold achieved!",
                "question_types": state.get("question_types", []),
                "completion_reason": state.get("session_completion_reason", "performance_achieved"),
                "adaptive_completion": True
            }
        
        state["next_question"] = question
        
        return {
            "next_question": question,
            "question_count": state["question_count"],
            "history": state["history"],
            "current_task": state.get("current_task"),
            "progress": state.get("progress"),
            "question_types": state.get("question_types", []),
            # Phase 5: Progress analytics
            "momentum_score": calculate_current_momentum(state),
            "difficulty_trend": get_difficulty_trend(state)
        }
    else:
        # We've already asked max_q questions for this topic
        # Phase 5: Update performance trends before moving to next topic
        update_performance_trends(state, current_topic)
        
        # See if there's another topic we can move to
        if state["current_topic_index"] + 1 < min(len(topics), max_t):
            state["current_topic_index"] += 1
            state["question_count"] = 1
            
            # Update current task and progress for due_items sessions
            if session_type == "due_items":
                new_topic_index = state["current_topic_index"]
                state["current_task"] = topics[new_topic_index]
                state["progress"] = f"{new_topic_index + 1}/{len(topics)} tasks"
            
            # Generate the first question for the next topic
            question = call_main_llm(state)
            
            # Handle early completion signal
            if question is None:
                state["done"] = True
                state["session_end_time"] = datetime.now(timezone.utc).isoformat()
                state["next_question"] = None
                
                return {
                    "done": True,
                    "history": state["history"],
                    "current_task": state.get("current_task"),
                    "progress": "Session completed",
                    "question_types": state.get("question_types", []),
                    "completion_reason": state.get("session_completion_reason", "all_topics_completed")
                }
            
            state["next_question"] = question
            
            return {
                "next_question": question,
                "current_topic_index": state["current_topic_index"],
                "question_count": state["question_count"],
                "history": state["history"],
                "current_task": state.get("current_task"),
                "progress": state.get("progress"),
                "question_types": state.get("question_types", []),
                # Phase 5: Topic transition analytics
                "topic_transition": True,
                "previous_topic_performance": get_topic_performance(state, topics[state["current_topic_index"] - 1])
            }
        else:
            # No more topics to cover: we are done
            state["done"] = True
            state["session_end_time"] = datetime.now(timezone.utc).isoformat()
            state["next_question"] = None
            state["session_completion_reason"] = "all_topics_completed"
            
            return {
                "done": True,
                "history": state["history"],
                "current_task": state.get("current_task"),
                "progress": "Session completed",
                "question_types": state.get("question_types", []),
                "completion_reason": "all_topics_completed",
                "session_duration": calculate_session_duration(state)
            }

def evaluate_node(state: GraphState) -> Dict[str, Any]:
    """
    Enhanced evaluator with Phase 5 advanced analytics and insights.
    
    Features:
    - Advanced performance analysis
    - Cross-topic connection detection
    - Learning momentum calculation
    - Retention prediction
    - Next session recommendations
    """
    if state["done"]:
        scores = call_evaluator_llm(state)
        
        # Ensure scores is valid - throw error if not
        if not scores or not isinstance(scores, dict):
            raise ValueError("Evaluation failed: call_evaluator_llm returned invalid scores")
        
        state["scores"] = scores
        
        # Add evaluation metadata for debugging and analytics
        session_type = state.get("session_type", "custom_topics")
        
        # Phase 5: Enhanced evaluation metadata
        evaluation_metadata = {
            "total_questions": len(state.get("history", [])),
            "topics_covered": len(state.get("topics", [])),
            "question_types_used": list(set(qt.get("type") for qt in state.get("question_types", []))),
            "session_type": session_type,
            "session_duration": calculate_session_duration(state),
            "completion_reason": state.get("session_completion_reason", "standard"),
            
            # Phase 5: Advanced metrics
            "learning_momentum": state.get("learning_momentum", 0.0),
            "learning_velocity": state.get("learning_velocity", 0.0),
            "average_confidence": calculate_average_confidence(state),
            "question_difficulty_range": get_difficulty_range(state),
            "adaptive_adjustments": count_adaptive_adjustments(state)
        }
        
        # Add FSRS-specific metadata for due_items sessions
        if session_type == "due_items":
            tasks = state.get("tasks", [])
            if tasks:
                evaluation_metadata.update({
                    "avg_difficulty": sum(t.difficulty for t in tasks) / len(tasks),
                    "total_overdue_days": sum(t.days_overdue for t in tasks),
                    "task_count": len(tasks)
                })
        
        # Phase 5: Generate comprehensive session summary
        session_summary = generate_session_summary(state, scores)
        
        return {
            "scores": scores,
            "session_type": session_type,
            "user_id": state.get("user_id"),
            "evaluation_metadata": evaluation_metadata,
            
            # Phase 5: Advanced analytics
            "topic_connections": state.get("topic_connections", {}),
            "cross_topic_insights": state.get("cross_topic_insights", []),
            "retention_predictions": state.get("retention_prediction", {}),
            "recommended_next_session": state.get("recommended_next_session", {}),
            "performance_trends": state.get("performance_trends", {}),
            "session_summary": session_summary,
            
            # Detailed performance analysis
            "detailed_analysis": {
                "confidence_scores": state.get("answer_confidence_scores", []),
                "difficulty_progression": state.get("question_difficulty_progression", []),
                "momentum_score": state.get("learning_momentum", 0.0),
                "velocity_score": state.get("learning_velocity", 0.0)
            }
        }
    
    return {}

# Phase 5: Helper functions for advanced analytics

def calculate_current_momentum(state: Dict) -> float:
    """Calculate current learning momentum during session"""
    history = state.get("history", [])
    if len(history) < 2:
        return 0.5  # Neutral momentum
    
    # Simple momentum based on recent answer quality
    recent_answers = history[-3:]  # Last 3 answers
    from my_agent.utils.tools import analyze_answer_quality
    
    quality_scores = []
    for qa in recent_answers:
        quality = analyze_answer_quality(qa.get("answer", ""))
        avg_quality = sum(quality.values()) / len(quality)
        quality_scores.append(avg_quality)
    
    if len(quality_scores) >= 2:
        # Momentum is the trend in quality
        momentum = (quality_scores[-1] - quality_scores[0]) / len(quality_scores)
        return max(0.0, min(1.0, 0.5 + momentum))
    
    return 0.5

def get_difficulty_trend(state: Dict) -> str:
    """Get the difficulty trend for current session"""
    progression = state.get("question_difficulty_progression", [])
    if len(progression) < 2:
        return "stable"
    
    recent_diff = progression[-3:]  # Last 3 questions
    if len(recent_diff) >= 2:
        if recent_diff[-1] > recent_diff[0]:
            return "increasing"
        elif recent_diff[-1] < recent_diff[0]:
            return "decreasing"
    
    return "stable"

def update_performance_trends(state: Dict, topic: str):
    """Update performance trends for a completed topic"""
    if "performance_trends" not in state:
        state["performance_trends"] = {}
    
    # Get scores for this topic from history
    topic_history = [qa for qa in state.get("history", []) if qa.get("topic") == topic]
    from my_agent.utils.tools import analyze_answer_quality
    
    quality_scores = []
    for qa in topic_history:
        quality = analyze_answer_quality(qa.get("answer", ""))
        avg_quality = sum(quality.values()) / len(quality)
        quality_scores.append(avg_quality)
    
    state["performance_trends"][topic] = quality_scores

def get_topic_performance(state: Dict, topic: str) -> Dict:
    """Get performance summary for a specific topic"""
    topic_history = [qa for qa in state.get("history", []) if qa.get("topic") == topic]
    
    if not topic_history:
        return {"questions": 0, "avg_quality": 0.0}
    
    from my_agent.utils.tools import analyze_answer_quality
    
    total_quality = 0
    for qa in topic_history:
        quality = analyze_answer_quality(qa.get("answer", ""))
        total_quality += sum(quality.values()) / len(quality)
    
    return {
        "questions": len(topic_history),
        "avg_quality": total_quality / len(topic_history)
    }

def calculate_session_duration(state: Dict) -> Dict:
    """Calculate session duration in various formats"""
    start_time_str = state.get("session_start_time")
    end_time_str = state.get("session_end_time")
    
    if not start_time_str:
        return {"seconds": 0, "minutes": 0, "formatted": "Unknown"}
    
    from datetime import datetime, timezone
    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
    
    if end_time_str:
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
    else:
        end_time = datetime.now(timezone.utc)
    
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    return {
        "seconds": total_seconds,
        "minutes": minutes,
        "formatted": f"{minutes}m {seconds}s"
    }

def calculate_average_confidence(state: Dict) -> float:
    """Calculate average confidence across all answers"""
    confidence_scores = state.get("answer_confidence_scores", [])
    if not confidence_scores:
        return 0.5
    
    return sum(confidence_scores) / len(confidence_scores)

def get_difficulty_range(state: Dict) -> Dict:
    """Get the range of question difficulties in the session"""
    progression = state.get("question_difficulty_progression", [])
    if not progression:
        return {"min": 0.5, "max": 0.5, "range": 0.0}
    
    return {
        "min": min(progression),
        "max": max(progression),
        "range": max(progression) - min(progression)
    }

def count_adaptive_adjustments(state: Dict) -> int:
    """Count how many adaptive adjustments were made during session"""
    # This would count session extensions, early completions, etc.
    adjustments = 0
    
    if state.get("session_completion_reason") == "performance_achieved":
        adjustments += 1
    
    # Count session extensions (if max_questions was increased)
    original_max = 7  # Default max questions
    current_max = state.get("max_questions", 7)
    if current_max > original_max:
        adjustments += (current_max - original_max) // 2  # Each extension adds 2 questions
    
    return adjustments

def generate_session_summary(state: Dict, scores: Dict) -> Dict:
    """Generate comprehensive session summary with insights"""
    topics = state.get("topics", [])
    total_questions = len(state.get("history", []))
    
    # Calculate averages
    avg_score = sum(scores.values()) / len(scores) if scores else 0
    session_duration = calculate_session_duration(state)
    
    # Performance categorization
    if avg_score >= 4.0:
        performance_level = "excellent"
        performance_message = "Outstanding performance! You've mastered these topics."
    elif avg_score >= 3.0:
        performance_level = "good"
        performance_message = "Good progress! Continue practicing to reinforce your understanding."
    elif avg_score >= 2.0:
        performance_level = "developing"
        performance_message = "You're developing understanding. Focus on fundamentals in your next session."
    else:
        performance_level = "needs_attention"
        performance_message = "These topics need more attention. Consider reviewing basics and practicing regularly."
    
    return {
        "performance_level": performance_level,
        "performance_message": performance_message,
        "total_topics": len(topics),
        "total_questions": total_questions,
        "average_score": round(avg_score, 1),
        "session_duration": session_duration,
        "completion_reason": state.get("session_completion_reason", "standard"),
        "learning_momentum": round(state.get("learning_momentum", 0.0), 2),
        "confidence_level": round(calculate_average_confidence(state), 2),
        "next_session_recommendation": state.get("recommended_next_session", {})
    }
