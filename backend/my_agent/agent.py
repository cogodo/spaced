import uuid
import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import logging
from datetime import datetime, timezone
import asyncio

from langgraph.graph import StateGraph

from my_agent.utils.state import GraphState
from my_agent.utils.nodes import (
    respond_node, evaluate_node, conversation_node, evaluate_topic_node, complete_session_with_topic_scores,
    question_maker_node, enhanced_conversation_node, question_summary_node, enhanced_scoring_node
)
from my_agent.utils.firebase_service import firebase_service, SessionMetrics
from my_agent.utils.tools import decide_topic_action, decide_after_evaluation

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_graph():
    """
    Build Phase 2: Question → Conversation → Scoring Architecture
    """
    # NOTE: We must pass state_schema=GraphState here to avoid a ValueError
    graph = StateGraph(state_schema=GraphState)

    # Add Phase 2 nodes
    graph.add_node("question_maker", question_maker_node)
    graph.add_node("enhanced_conversation", enhanced_conversation_node) 
    graph.add_node("question_summary", question_summary_node)
    graph.add_node("enhanced_scoring", enhanced_scoring_node)
    graph.add_node("complete_session", complete_session_with_topic_scores)

    # Set entry point to question maker
    graph.set_entry_point("question_maker")

    # Define conditional edges for Phase 2 architecture
    graph.add_conditional_edges(
        "question_maker",
        route_from_question_maker,
        {
            "present_question": "enhanced_conversation",
            "topic_complete": "enhanced_scoring",
            "session_complete": "complete_session",
            "error": "complete_session"
        }
    )

    graph.add_conditional_edges(
        "enhanced_conversation", 
        route_from_conversation,
        {
            "continue_conversation": "enhanced_conversation",
            "question_complete": "question_summary",
            "next_topic": "enhanced_scoring",
            "end_session": "complete_session",
            "error": "complete_session"
        }
    )

    graph.add_conditional_edges(
        "question_summary",
        route_from_question_summary,
        {
            "next_question": "question_maker",
            "topic_complete": "enhanced_scoring",
            "error": "complete_session"
        }
    )

    graph.add_conditional_edges(
        "enhanced_scoring",
        route_from_scoring,
        {
            "next_topic": "question_maker", 
            "session_complete": "complete_session",
            "error": "complete_session"
        }
    )

    # complete_session is terminal - no outgoing edges

    return graph.compile()


def route_from_question_maker(state: GraphState) -> str:
    """Route from question_maker_node based on its output"""
    # The node result is stored directly in state by LangGraph
    # Look for the action field that should be set by the node
    action = "error"  # Default fallback
    
    # Check if there's a current question (indicates successful question presentation)
    if state.get("current_question"):
        action = "present_question"
    # Check if session should be complete
    elif state.get("session_complete"):
        action = "session_complete"
    # Check topic completion signals
    elif not state.get("topics") or len(state.get("completed_topics", [])) >= len(state.get("topics", [])):
        action = "session_complete"
    else:
        # This might be topic_complete or error - check remaining topics
        remaining = get_remaining_topics(state)
        if not remaining:
            action = "session_complete"
        else:
            action = "topic_complete"  # No questions available for current topic
    
    logger.info(f"Routing from question_maker: action={action}")
    return action


def route_from_conversation(state: GraphState) -> str:
    """Route from enhanced_conversation_node based on its output"""
    user_input = state.get("user_input", "").lower()
    
    # Check for explicit user signals first
    if "end session" in user_input or "quit" in user_input or "stop" in user_input:
        logger.info("User requested to end session")
        return "end_session"
    
    if "next topic" in user_input or "move to next topic" in user_input:
        logger.info("User requested to move to next topic")
        return "next_topic"
    
    # Check if current question conversation is marked complete
    current_question = state.get("current_question")
    if not current_question:
        # No active question suggests completion
        logger.info("No current question - routing to question_complete")
        return "question_complete"
    
    # Check conversation history length to determine if we should continue
    conversation_history = current_question.get("conversation_history", [])
    if len(conversation_history) > 10:  # Prevent overly long conversations
        logger.info("Conversation getting long - routing to question_complete")
        return "question_complete"
    
    # Default to continue conversation
    logger.info("Continuing conversation")
    return "continue_conversation"


def route_from_question_summary(state: GraphState) -> str:
    """Route from question_summary_node based on its output"""
    # Check how many questions have been completed for current topic
    topic_summaries = state.get("topic_question_summaries", [])
    session_settings = state.get("session_settings", {})
    max_questions = session_settings.get("max_questions_per_topic", 7)
    
    # Check if user wants to move to next topic
    user_input = state.get("user_input", "").lower()
    if any(signal in user_input for signal in ["next topic", "move to next", "done with this topic"]):
        logger.info("User requested next topic")
        return "topic_complete"
    
    # Check if we've reached max questions for this topic
    if len(topic_summaries) >= max_questions:
        logger.info(f"Reached max questions ({max_questions}) for topic")
        return "topic_complete"
    
    # Default to next question
    logger.info("Continuing with next question")
    return "next_question"


def route_from_scoring(state: GraphState) -> str:
    """Route from enhanced_scoring_node based on its output"""
    # Check if there are remaining topics
    remaining_topics = get_remaining_topics(state)
    
    if remaining_topics:
        logger.info(f"Moving to next topic: {remaining_topics[0] if remaining_topics else 'None'}")
        return "next_topic"
    else:
        logger.info("All topics completed - ending session")
        return "session_complete"


# Legacy graph builder for backward compatibility
def build_legacy_graph():
    """
    Build legacy Topic-Aware Agentic LangGraph with conditional edges and AI decision making
    """
    # NOTE: We must pass state_schema=GraphState here to avoid a ValueError
    graph = StateGraph(state_schema=GraphState)

    # Add the legacy nodes
    graph.add_node("conversation", conversation_node)
    graph.add_node("evaluate_topic", evaluate_topic_node) 
    graph.add_node("complete_session", complete_session_with_topic_scores)

    # Set entry point
    graph.set_entry_point("conversation")

    # Add conditional edges with AI decision making
    graph.add_conditional_edges(
        "conversation",
        decide_topic_action,  # AI decides: continue_topic, evaluate_topic, or end_session
        {
            "continue_topic": "conversation",
            "evaluate_topic": "evaluate_topic",
            "end_session": "complete_session"
        }
    )

    graph.add_conditional_edges(
        "evaluate_topic",
        decide_after_evaluation,  # AI decides: next_topic or end_session
        {
            "next_topic": "conversation",
            "end_session": "complete_session"
        }
    )

    # complete_session is terminal - no outgoing edges

    return graph.compile()


# Use Phase 2 architecture by default
compiled_graph = build_graph()

# For debugging/testing, also compile legacy graph
legacy_compiled_graph = build_legacy_graph()

# In‐memory store of session_id -> GraphState
SESSIONS: Dict[str, GraphState] = {}

# Session start times for analytics
SESSION_START_TIMES: Dict[str, datetime] = {}


class StartPayload(BaseModel):
    session_type: str  # "due_items" or "custom_topics"
    user_id: Optional[str] = None  # For due_items (or provide via token)
    topics: Optional[list[str]] = None  # For custom_topics
    max_topics: int = 3
    max_questions: int = 7
    
    # Phase 5: Adaptive session features
    adaptive_session_length: bool = True  # Enable adaptive session length
    performance_threshold: float = 4.5    # Score threshold for early completion
    struggle_threshold: float = 2.0       # Score threshold for session extension
    personalized_difficulty: bool = True  # Use personalized difficulty adaptation


class AnswerPayload(BaseModel):
    session_id: str
    user_input: str


async def get_user_id(
    payload: StartPayload = None,
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """Extract user ID from payload or verify Firebase token"""
    try:
        # For due_items sessions, we need user authentication
        if payload and payload.session_type == "due_items":
            if payload.user_id:
                return payload.user_id
            elif authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
                user_id = await firebase_service.verify_user_token(token)
                return user_id
            else:
                raise HTTPException(
                    status_code=401, 
                    detail="Authentication required for due_items sessions"
                )
        
        # For custom_topics, user_id is optional
        return payload.user_id if payload else None
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# Get environment variables
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://getspaced.app,https://www.getspaced.app,http://localhost:3000,http://localhost:8080").split(",")

app = FastAPI(
    title="Spaced Learning API",
    description="AI-powered spaced repetition learning API with FSRS integration",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Spaced Learning API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "sessions_count": len(SESSIONS)}


@app.get("/due_tasks/{user_id}")
async def check_due_tasks(user_id: str):
    """Check how many tasks are due for a user without starting a session"""
    try:
        due_tasks = await firebase_service.get_due_tasks(user_id)
        
        return {
            "user_id": user_id,
            "due_tasks_count": len(due_tasks),
            "has_due_tasks": len(due_tasks) > 0,
            "tasks_preview": [
                {
                    "name": task.task_name,
                    "difficulty": task.difficulty,
                    "days_overdue": task.days_overdue
                } 
                for task in due_tasks[:5]  # Show first 5 tasks as preview
            ] if due_tasks else [],
            "message": f"You have {len(due_tasks)} tasks due for review" if due_tasks else "All caught up! No tasks due for review."
        }
        
    except Exception as e:
        logger.error(f"Error checking due tasks for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking due tasks: {str(e)}")


@app.get("/dashboard/{user_id}")
async def get_user_dashboard(user_id: str):
    """Get comprehensive dashboard data for user"""
    try:
        dashboard_data = await firebase_service.get_user_dashboard_data(user_id)
        
        if not dashboard_data:
            return {
                "user_id": user_id,
                "message": "No data available yet. Complete some sessions to see your progress!",
                "current_status": {"due_tasks_count": 0},
                "weekly_progress": {"sessions_completed": 0},
                "recommendations": {"suggested_session_type": "custom_topics"}
            }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error generating dashboard for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating dashboard: {str(e)}")


@app.get("/insights/{user_id}")
async def get_learning_insights(user_id: str, days: int = 30):
    """Get detailed learning insights for a user"""
    try:
        insights = await firebase_service.get_learning_insights(user_id, days)
        
        if not insights:
            return {
                "user_id": user_id,
                "message": f"No session data found for the last {days} days. Start learning to see insights!",
                "analysis_period_days": days
            }
        
        # Convert insights to dictionary for JSON response
        return {
            "user_id": insights.user_id,
            "analysis_period_days": insights.analysis_period_days,
            "session_statistics": {
                "total_sessions": insights.total_sessions,
                "due_items_sessions": insights.due_items_sessions,
                "custom_topics_sessions": insights.custom_topics_sessions,
                "total_study_time_minutes": insights.total_study_time_minutes,
                "avg_session_duration_minutes": round(insights.avg_session_duration_minutes, 1)
            },
            "performance_analysis": {
                "average_scores": insights.average_scores,
                "improvement_rate": insights.improvement_rate,
                "struggling_topics": insights.struggling_topics,
                "mastered_topics": insights.mastered_topics
            },
            "recommendations": {
                "review_frequency": insights.recommended_review_frequency,
                "focus_areas": insights.struggling_topics[:3]
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


@app.post("/optimize_session")
async def optimize_session_settings(user_id: str, session_type: str):
    """
    Phase 5: Get optimized session settings based on user performance history
    """
    try:
        # Get user insights to inform optimization
        insights = await firebase_service.get_learning_insights(user_id, days=14)  # Last 2 weeks
        
        if not insights:
            # Default settings for new users
            return {
                "user_id": user_id,
                "optimized_settings": {
                    "max_topics": 3,
                    "max_questions": 7,
                    "adaptive_session_length": True,
                    "performance_threshold": 4.5,
                    "struggle_threshold": 2.0,
                    "estimated_duration_minutes": 15
                },
                "reasoning": "Default settings for new user - will adapt based on your performance",
                "personalization_level": "none"
            }
        
        # Analyze user performance to optimize settings
        avg_score = sum(insights.average_scores.values()) / len(insights.average_scores) if insights.average_scores else 3.0
        avg_session_duration = insights.avg_session_duration_minutes
        
        # Optimize based on performance patterns
        optimized_settings = {
            "adaptive_session_length": True,  # Always enable for advanced users
            "personalized_difficulty": True
        }
        
        # Adjust max topics based on performance and attention span
        if avg_score >= 4.0 and avg_session_duration <= 20:
            # High performer, efficient sessions
            optimized_settings.update({
                "max_topics": 4,
                "max_questions": 5,
                "performance_threshold": 4.5,
                "struggle_threshold": 2.5,
                "estimated_duration_minutes": 12
            })
            reasoning = "Optimized for high performance - challenging but efficient sessions"
            personalization = "high"
            
        elif avg_score >= 3.0:
            # Good performer, standard sessions
            optimized_settings.update({
                "max_topics": 3,
                "max_questions": 7,
                "performance_threshold": 4.0,
                "struggle_threshold": 2.0,
                "estimated_duration_minutes": 15
            })
            reasoning = "Balanced settings for steady progress"
            personalization = "medium"
            
        elif avg_score >= 2.0:
            # Developing learner, supportive sessions
            optimized_settings.update({
                "max_topics": 2,
                "max_questions": 8,
                "performance_threshold": 3.5,
                "struggle_threshold": 1.5,
                "estimated_duration_minutes": 18
            })
            reasoning = "Focused sessions to build confidence and understanding"
            personalization = "medium"
            
        else:
            # Struggling learner, gentle approach
            optimized_settings.update({
                "max_topics": 2,
                "max_questions": 10,
                "performance_threshold": 3.0,
                "struggle_threshold": 1.0,
                "estimated_duration_minutes": 20
            })
            reasoning = "Extended, supportive sessions to build foundational understanding"
            personalization = "high"
        
        # Session type specific adjustments
        if session_type == "due_items":
            # Due items tend to be more challenging
            optimized_settings["struggle_threshold"] -= 0.2
            optimized_settings["estimated_duration_minutes"] += 3
            reasoning += " | Adjusted for due items review"
        
        # Special considerations for struggling topics
        if insights.struggling_topics and len(insights.struggling_topics) > len(insights.mastered_topics):
            optimized_settings["max_questions"] += 2
            optimized_settings["performance_threshold"] -= 0.3
            reasoning += " | Extended practice for struggling areas"
        
        return {
            "user_id": user_id,
            "session_type": session_type,
            "optimized_settings": optimized_settings,
            "reasoning": reasoning,
            "personalization_level": personalization,
            "based_on_data": {
                "sessions_analyzed": insights.total_sessions,
                "avg_performance": round(avg_score, 1),
                "avg_duration_minutes": round(avg_session_duration, 1),
                "struggling_topics_count": len(insights.struggling_topics),
                "mastered_topics_count": len(insights.mastered_topics)
            }
        }
        
    except Exception as e:
        logger.error(f"Error optimizing session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing session: {str(e)}")


@app.get("/session_analytics/{session_id}")
async def get_session_analytics(session_id: str):
    """
    Phase 5: Get real-time analytics for an active session
    """
    try:
        if session_id not in SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = SESSIONS[session_id]
        
        # Calculate real-time analytics
        from my_agent.utils.nodes import (
            calculate_current_momentum, get_difficulty_trend, 
            calculate_average_confidence, get_difficulty_range,
            calculate_session_duration
        )
        
        analytics = {
            "session_id": session_id,
            "session_type": state.get("session_type"),
            "current_progress": {
                "topic_index": state.get("current_topic_index", 0),
                "total_topics": len(state.get("topics", [])),
                "question_count": state.get("question_count", 0),
                "total_questions": len(state.get("history", [])),
                "current_task": state.get("current_task"),
                "progress_text": state.get("progress")
            },
            "performance_metrics": {
                "learning_momentum": calculate_current_momentum(state),
                "difficulty_trend": get_difficulty_trend(state),
                "average_confidence": calculate_average_confidence(state),
                "question_difficulty_range": get_difficulty_range(state)
            },
            "session_timing": calculate_session_duration(state),
            "adaptive_features": {
                "adaptive_mode": state.get("adaptive_session_length", False),
                "performance_threshold": state.get("performance_threshold", 4.5),
                "struggle_threshold": state.get("struggle_threshold", 2.0),
                "completion_reason": state.get("session_completion_reason")
            },
            "question_analytics": {
                "types_used": list(set(qt.get("type", "unknown") for qt in state.get("question_types", []))),
                "type_distribution": {}
            }
        }
        
        # Calculate question type distribution
        question_types = state.get("question_types", [])
        for qt in question_types:
            qtype = qt.get("type", "unknown")
            analytics["question_analytics"]["type_distribution"][qtype] = analytics["question_analytics"]["type_distribution"].get(qtype, 0) + 1
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session analytics for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session analytics: {str(e)}")


@app.post("/start_session")
async def start_session(payload: StartPayload, user_id: Optional[str] = Depends(get_user_id)):
    """
    Start a new learning session with topic-aware initialization
    """
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"Starting new session {session_id}")
        
        # Initialize new state structure
        state = {
            "session_type": payload.session_type,
            "user_id": user_id,
            "session_id": session_id,
            "message_count": 0,
            "max_messages": 40,  # Hard limit
            "current_topic_index": 0,
            "completed_topics": [],
            "topic_scores": {},
            "topic_evaluations": {},
            "conversation_history": [],
            "session_complete": False,
            "session_summary": None,
            "topic_sources": {},
            
            # Initialize user_input as None for first call
            "user_input": None,
            "next_question": None,
            
            # PHASE 2: Question-Based Conversation Fields
            "current_question": None,
            "current_topic_id": None,
            "topic_question_summaries": [],
            "session_settings": {
                "max_questions_per_topic": payload.max_questions,
                "adaptive_session_length": payload.adaptive_session_length,
                "performance_threshold": payload.performance_threshold,
                "struggle_threshold": payload.struggle_threshold,
                "personalized_difficulty": payload.personalized_difficulty
            },
            
            # Legacy fields for backward compatibility (TODO: remove after full migration)
            "topics": [],
            "tasks": None,
            "question_count": 0,
            "history": [],
            "done": False,
            "scores": None,
            "max_topics": payload.max_topics,
            "max_questions": payload.max_questions,
            "due_tasks_count": None,
            "current_task": None,
            "progress": None,
            "question_types": []
        }
        
        # Session type specific initialization
        if payload.session_type == "due_items":
            if not user_id:
                raise HTTPException(status_code=401, detail="User ID required for due_items sessions")
            
            # Fetch due tasks from Firebase
            due_tasks = await firebase_service.get_due_tasks(user_id)
            
            if not due_tasks:
                return {
                    "message": "No tasks due for review! You're all caught up.",
                    "due_tasks_count": 0,
                    "session_id": None
                }
            
            # Limit topics to max_topics
            limited_tasks = due_tasks[:payload.max_topics]
            
            # Store in new format
            state["due_tasks"] = limited_tasks
            state["topics"] = [task.task_name for task in limited_tasks]
            
            # Also store in legacy format for backward compatibility
            state["tasks"] = limited_tasks
            state["due_tasks_count"] = len(due_tasks)
            
            logger.info(f"Session {session_id}: {len(limited_tasks)} due tasks loaded for user {user_id}")
            
        elif payload.session_type == "custom_topics":
            if not payload.topics:
                raise HTTPException(status_code=400, detail="Topics required for custom_topics sessions")
            
            # Limit topics to max_topics  
            limited_topics = payload.topics[:payload.max_topics]
            
            # Store in new format
            state["custom_topics"] = limited_topics
            state["topics"] = limited_topics
            
            logger.info(f"Session {session_id}: {len(limited_topics)} custom topics loaded")
            
        else:
            raise HTTPException(status_code=400, detail="Invalid session_type")
        
        # Store session
        SESSIONS[session_id] = state
        SESSION_START_TIMES[session_id] = datetime.now()
        
        # Get initial response from conversation node
        try:
            result = await asyncio.to_thread(compiled_graph.invoke, state)
            
            # Update stored state with result
            SESSIONS[session_id].update(result)
            
            return {
                "session_id": session_id,
                "message": result.get("next_question", "Session started"),
                "current_topic": result.get("current_topic"),
                "remaining_topics": result.get("remaining_topics", []),
                "message_count": result.get("message_count", 0),
                "total_topics": len(state["topics"]),
                "session_type": payload.session_type,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error invoking graph for session {session_id}: {e}")
            # Clean up failed session
            SESSIONS.pop(session_id, None)
            SESSION_START_TIMES.pop(session_id, None)
            raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error starting session: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/answer")
async def answer_question(payload: AnswerPayload):
    """
    Process user answer in the agentic conversation system
    """
    try:
        session_id = payload.session_id
        user_input = payload.user_input.strip()
        
        if not user_input:
            raise HTTPException(status_code=400, detail="User input cannot be empty")
        
        # Retrieve the session
        if session_id not in SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = SESSIONS[session_id]
        
        # Check if session is complete
        if state.get("session_complete", False):
            return {
                "session_complete": True,
                "message": "This session has already been completed.",
                "session_summary": state.get("session_summary")
            }
        
        # Check message limit
        if state.get("message_count", 0) >= state.get("max_messages", 40):
            # Force session completion
            from my_agent.utils.nodes import complete_session_with_topic_scores
            final_result = complete_session_with_topic_scores(state)
            SESSIONS[session_id].update(final_result)
            
            return {
                "session_complete": True,
                "message": "Session completed - message limit reached.",
                "session_summary": final_result.get("session_summary"),
                "topic_scores": final_result.get("topic_scores")
            }
        
        # Set user input for next graph invocation
        state["user_input"] = user_input
        
        # Invoke the graph to get AI response
        try:
            result = await asyncio.to_thread(compiled_graph.invoke, state)
            
            # Update stored state
            SESSIONS[session_id].update(result)
            
            # Check if session is complete after this turn
            if result.get("session_complete", False):
                return {
                    "session_complete": True,
                    "message": "Session completed successfully!",
                    "session_summary": result.get("session_summary"),
                    "topic_scores": result.get("topic_scores"),
                    "topics_completed": result.get("topics_completed"),
                    "total_topics": result.get("total_topics")
                }
            
            # Check if we just completed a topic evaluation
            if result.get("topic_evaluated"):
                evaluated_topic = result.get("topic_evaluated")
                topic_score = result.get("topic_score")
                remaining_topics = result.get("remaining_topics", [])
                
                return {
                    "topic_completed": True,
                    "topic_evaluated": evaluated_topic,
                    "topic_score": topic_score,
                    "message": f"Great work on {evaluated_topic}! " + (
                        f"Next, let's discuss {remaining_topics[0]}." if remaining_topics 
                        else "Let's wrap up the session."
                    ),
                    "remaining_topics": remaining_topics,
                    "topics_completed": result.get("topics_completed", 0),
                    "session_complete": False
                }
            
            # Regular conversation response
            return {
                "message": result.get("next_question", "Let's continue our conversation."),
                "current_topic": result.get("current_topic"),
                "remaining_topics": result.get("remaining_topics", []),
                "message_count": result.get("message_count", 0),
                "max_messages": state.get("max_messages", 40),
                "session_complete": False,
                "conversation_action": result.get("conversation_action", "continue")
            }
            
        except Exception as e:
            logger.error(f"Error invoking graph for session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing answer: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in answer endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/complete_session")
async def complete_session(session_id: str):
    """Complete a session and return scores formatted for frontend FSRS with Phase 5 analytics"""
    try:
        if session_id not in SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = SESSIONS[session_id]
        
        if not state.get("done"):
            raise HTTPException(status_code=400, detail="Session not yet completed")
        
        scores = state.get("scores", {})
        
        # Phase 5: Enhanced session completion with advanced analytics
        completion_response = {
            "scores": scores,
            "session_summary": state.get("session_summary", {}),
            
            # Advanced analytics
            "performance_analysis": {
                "learning_momentum": state.get("learning_momentum", 0.0),
                "learning_velocity": state.get("learning_velocity", 0.0),
                "average_confidence": state.get("detailed_analysis", {}).get("confidence_scores", []),
                "completion_reason": state.get("session_completion_reason", "standard")
            },
            
            # Topic insights
            "topic_insights": {
                "connections_discovered": state.get("cross_topic_insights", []),
                "retention_predictions": state.get("retention_prediction", {}),
                "performance_trends": state.get("performance_trends", {})
            },
            
            # Next session recommendations
            "recommendations": state.get("recommended_next_session", {}),
            
            # Session metadata
            "session_metadata": {
                "total_questions": len(state.get("history", [])),
                "question_types_used": list(set(qt.get("type", "unknown") for qt in state.get("question_types", []))),
                "adaptive_adjustments": state.get("evaluation_metadata", {}).get("adaptive_adjustments", 0),
                "session_duration": state.get("evaluation_metadata", {}).get("session_duration", {}),
                "difficulty_range": state.get("detailed_analysis", {}).get("difficulty_progression", [])
            }
        }
        
        # For due_items sessions, provide formatted data for FSRS
        if state.get("session_type") == "due_items" and state.get("user_id"):
            completion_response.update({
                "tasks_for_fsrs_update": scores,
                "user_id": state["user_id"],
                "fsrs_insights": {
                    "difficulty_adaptations": state.get("evaluation_metadata", {}).get("avg_difficulty"),
                    "overdue_items_addressed": state.get("evaluation_metadata", {}).get("task_count", 0)
                }
            })
            
            # Enhanced Firebase updates with session metadata
            for task_name, score in scores.items():
                session_data = {
                    "session_type": state.get("session_type"),
                    "question_types": [qt.get("type") for qt in state.get("question_types", []) if qt.get("topic") == task_name],
                    "difficulty_adaptation": True,
                    "answer_quality": "enhanced",
                    "completion_reason": state.get("session_completion_reason"),
                    "learning_momentum": state.get("learning_momentum", 0.0),
                    "confidence_level": state.get("detailed_analysis", {}).get("confidence_scores", [])
                }
                await firebase_service.update_task_after_review(
                    state["user_id"], task_name, score, session_data
                )
        
        # Clean up session
        del SESSIONS[session_id]
        if session_id in SESSION_START_TIMES:
            del SESSION_START_TIMES[session_id]
        logger.info(f"Phase 5 session {session_id} completed with advanced analytics")
        
        return completion_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error completing session: {str(e)}")


async def generate_and_save_session_metrics(session_id: str, state: GraphState):
    """Generate comprehensive session metrics and save to Firebase"""
    try:
        if session_id not in SESSION_START_TIMES or not state.get("user_id"):
            logger.warning(f"Cannot generate metrics for session {session_id} - missing data")
            return
        
        start_time = SESSION_START_TIMES[session_id]
        end_time = datetime.now(timezone.utc)
        duration = int((end_time - start_time).total_seconds())
        
        # Analyze question types and distribution
        question_types = state.get("question_types", [])
        question_types_used = list(set(qt.get("type") for qt in question_types))
        question_type_distribution = {}
        for qt in question_types:
            qtype = qt.get("type", "unknown")
            question_type_distribution[qtype] = question_type_distribution.get(qtype, 0) + 1
        
        # Calculate questions per topic
        questions_per_topic = {}
        for qt in question_types:
            topic = qt.get("topic", "unknown")
            questions_per_topic[topic] = questions_per_topic.get(topic, 0) + 1
        
        # Performance metrics
        scores = state.get("scores", {})
        average_score = sum(scores.values()) / len(scores) if scores else 0
        score_variance = sum((score - average_score) ** 2 for score in scores.values()) / len(scores) if scores else 0
        
        # FSRS-specific metrics for due_items sessions
        initial_difficulties = None
        avg_initial_difficulty = None
        overdue_items_count = None
        total_overdue_days = None
        
        if state.get("session_type") == "due_items" and state.get("tasks"):
            initial_difficulties = {task.task_name: task.difficulty for task in state["tasks"]}
            avg_initial_difficulty = sum(initial_difficulties.values()) / len(initial_difficulties)
            overdue_items_count = sum(1 for task in state["tasks"] if task.days_overdue > 0)
            total_overdue_days = sum(task.days_overdue for task in state["tasks"])
        
        # Create comprehensive metrics
        metrics = SessionMetrics(
            session_id=session_id,
            user_id=state["user_id"],
            session_type=state.get("session_type", "custom_topics"),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            topics_covered=state.get("topics", []),
            total_questions=len(state.get("history", [])),
            questions_per_topic=questions_per_topic,
            question_types_used=question_types_used,
            question_type_distribution=question_type_distribution,
            scores=scores,
            average_score=average_score,
            score_variance=score_variance,
            initial_difficulties=initial_difficulties,
            avg_initial_difficulty=avg_initial_difficulty,
            overdue_items_count=overdue_items_count,
            total_overdue_days=total_overdue_days
        )
        
        # Save to Firebase
        success = await firebase_service.save_session_metrics(metrics)
        if success:
            logger.info(f"Session metrics saved successfully for session {session_id}")
        else:
            logger.error(f"Failed to save session metrics for session {session_id}")
            
    except Exception as e:
        logger.error(f"Error generating session metrics for {session_id}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("my_agent.agent:app", host=HOST, port=PORT, reload=False)
