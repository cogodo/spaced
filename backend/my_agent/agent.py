import uuid
import os
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, Any
import logging
from datetime import datetime, timezone
import asyncio
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from langgraph.graph import StateGraph, END

from my_agent.utils.state import GraphState
from my_agent.utils.nodes import (
    conversation_node, evaluate_topic_node, complete_session_with_topic_scores
)
from my_agent.utils.firebase_service import firebase_service, SessionMetrics
from my_agent.utils.tools import get_remaining_topics, decide_topic_action, decide_after_evaluation
from my_agent.utils.adaptive_state_integration import auto_restore_adaptive_state

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def session_initialization_node(state: GraphState) -> Dict[str, Any]:
    """
    Initialize session with welcome message and topic introduction.
    This handles the initial session setup that was missing from question_maker_node.
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


def build_session_init_graph():
    """
    Build graph for session initialization only
    """
    graph = StateGraph(state_schema=GraphState)
    graph.add_node("session_init", session_initialization_node)
    graph.set_entry_point("session_init")
    graph.add_edge("session_init", END)
    return graph.compile()


def build_conversation_graph():
    """
    Build graph for conversation flow (answer processing)
    """
    graph = StateGraph(state_schema=GraphState)
    
    # Add conversation nodes
    graph.add_node("conversation", conversation_node)
    graph.add_node("evaluate_topic", evaluate_topic_node)
    graph.add_node("complete_session", complete_session_with_topic_scores)

    # Set entry point to conversation
    graph.set_entry_point("conversation")

    # Define conditional edges for conversation flow
    graph.add_conditional_edges(
        "conversation",
        route_from_conversation,
        {
            "continue_topic": "conversation",
            "evaluate_topic": "evaluate_topic",
            "end_session": "complete_session",
            "error": "complete_session"
        }
    )

    graph.add_conditional_edges(
        "evaluate_topic",
        route_from_evaluation,
        {
            "next_topic": "conversation",
            "end_session": "complete_session",
            "error": "complete_session"
        }
    )

    # complete_session is terminal
    graph.add_edge("complete_session", END)
    
    return graph.compile()


def build_graph():
    """
    Build Phase 4: Simplified but Working LangGraph Architecture
    """
    # NOTE: We must pass state_schema=GraphState here to avoid a ValueError
    graph = StateGraph(state_schema=GraphState)

    # Add Phase 4 nodes (using existing working nodes)
    graph.add_node("session_init", session_initialization_node)
    graph.add_node("conversation", conversation_node)
    graph.add_node("evaluate_topic", evaluate_topic_node)
    graph.add_node("complete_session", complete_session_with_topic_scores)

    # Set entry point to session initialization
    graph.set_entry_point("session_init")
    
    # Route from session initialization directly to END (no conversation loop)
    graph.add_edge("session_init", END)

    # Define conditional edges for Phase 4 architecture
    graph.add_conditional_edges(
        "conversation",
        route_from_conversation,
        {
            "continue_topic": "conversation",
            "evaluate_topic": "evaluate_topic",
            "end_session": "complete_session",
            "error": "complete_session"
        }
    )

    graph.add_conditional_edges(
        "evaluate_topic",
        route_from_evaluation,
        {
            "next_topic": "conversation",
            "end_session": "complete_session",
            "error": "complete_session"
        }
    )

    # complete_session is terminal - add edge to END
    graph.add_edge("complete_session", END)

    return graph.compile()


def route_from_conversation(state: GraphState) -> str:
    """Route from conversation_node - Phase 4 with legacy rejection"""
    # REJECT LEGACY PATTERNS
    user_input = state.get("user_input", "")
    if user_input and any(legacy_term in user_input.lower() for legacy_term in ['use_legacy', 'old_system', 'legacy_mode']):
        logger.error("Legacy system usage attempted - rejecting")
        return "error"
    
    # Import the decision function from tools
    from my_agent.utils.tools import decide_topic_action
    
    try:
        decision = decide_topic_action(state)
        logger.info(f"Conversation routing decision: {decision}")
        
        # Map decisions to valid graph edges
        if decision == "continue_topic":
            return "continue_topic"
        elif decision == "evaluate_topic":
            return "evaluate_topic"
        elif decision == "end_session":
            return "end_session"
        else:
            logger.warning(f"Unknown decision: {decision}, defaulting to continue_topic")
            return "continue_topic"
            
    except Exception as e:
        logger.error(f"Error in conversation routing: {e}")
        return "error"


def route_from_evaluation(state: GraphState) -> str:
    """Route from evaluate_topic_node - Phase 4 with legacy rejection"""
    # REJECT LEGACY PATTERNS
    if not state.get("session_settings"):
        logger.error("Legacy session format detected - rejecting")
        return "error"
    
    # Import the decision function from tools
    from my_agent.utils.tools import decide_after_evaluation
    
    try:
        decision = decide_after_evaluation(state)
        logger.info(f"Evaluation routing decision: {decision}")
        
        # Map decisions to valid graph edges
        if decision == "next_topic":
            return "next_topic"
        elif decision == "end_session":
            return "end_session"
        else:
            logger.warning(f"Unknown decision: {decision}, defaulting to end_session")
            return "end_session"
            
    except Exception as e:
        logger.error(f"Error in evaluation routing: {e}")
        return "error"


# Use Phase 4 architecture - NEW LANGGRAPH SYSTEM ONLY
session_init_graph = build_session_init_graph()
conversation_graph = build_conversation_graph()
compiled_graph = build_graph()  # Keep for backward compatibility

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

# Phase 4 Production: Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)


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
@limiter.limit("10/minute")  # Allow 10 session starts per minute per IP
async def start_session(request: Request, payload: StartPayload, user_id: Optional[str] = Depends(get_user_id)):
    """
    Start a new learning session with Phase 4 LangGraph architecture ONLY
    """
    try:
        # REJECT LEGACY USAGE PATTERNS
        if hasattr(payload, 'legacy_mode') or hasattr(payload, 'use_old_system'):
            raise HTTPException(
                status_code=400, 
                detail="Legacy system is no longer supported. Use Phase 4 LangGraph architecture only."
            )
        
        session_id = str(uuid.uuid4())
        logger.info(f"Starting new Phase 4 session {session_id}")
        
        # Initialize Phase 4 state structure ONLY
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
            
            # PHASE 4: Question-Based Conversation Fields
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
            
            # Core topic management
            "topics": [],
            "max_topics": payload.max_topics,
            "max_questions": payload.max_questions
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
            
            # Store in Phase 4 format
            state["due_tasks"] = limited_tasks
            state["topics"] = [task.task_name for task in limited_tasks]
            
            logger.info(f"Session {session_id}: {len(limited_tasks)} due tasks loaded for user {user_id}")
            
        elif payload.session_type == "custom_topics":
            if not payload.topics:
                raise HTTPException(status_code=400, detail="Topics required for custom_topics sessions")
            
            # Limit topics to max_topics  
            limited_topics = payload.topics[:payload.max_topics]
            
            # Store in Phase 4 format
            state["custom_topics"] = limited_topics
            state["topics"] = limited_topics
            
            logger.info(f"Session {session_id}: {len(limited_topics)} custom topics loaded")
            
        else:
            raise HTTPException(status_code=400, detail="Invalid session_type")
        
        # Store session
        SESSIONS[session_id] = state
        SESSION_START_TIMES[session_id] = datetime.now()
        
        # PHASE 4 PRODUCTION: Restore adaptive state if this is a continuing session
        # For new sessions, this will initialize with default adaptive state
        if user_id:
            try:
                restoration_success = await auto_restore_adaptive_state(session_id, user_id, state)
                if restoration_success:
                    logger.info(f"Restored adaptive state for session {session_id}")
                else:
                    logger.info(f"Initialized default adaptive state for session {session_id}")
            except Exception as e:
                logger.warning(f"Error restoring adaptive state for session {session_id}: {e}")
                # Continue with session even if state restoration fails
        
        # Get initial response from session initialization
        try:
            result = await asyncio.to_thread(session_init_graph.invoke, state)
            
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
            logger.error(f"Error invoking session initialization for session {session_id}: {e}")
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
@limiter.limit("30/minute")  # Allow 30 answers per minute per IP
async def answer_question(request: Request, payload: AnswerPayload):
    """
    Process user answer in the Phase 4 LangGraph conversation system ONLY
    """
    try:
        session_id = payload.session_id
        user_input = payload.user_input.strip()
        
        if not user_input:
            raise HTTPException(status_code=400, detail="User input cannot be empty")
        
        # REJECT LEGACY USAGE PATTERNS
        if any(legacy_term in user_input.lower() for legacy_term in ['use_legacy', 'old_system', 'legacy_mode']):
            raise HTTPException(
                status_code=400, 
                detail="Legacy system commands are not supported. Use Phase 4 LangGraph system only."
            )
        
        # Retrieve the session
        if session_id not in SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = SESSIONS[session_id]
        
        # VERIFY PHASE 4 SESSION
        if not state.get("session_settings") or "current_question" not in state:
            raise HTTPException(
                status_code=400, 
                detail="Invalid session format. Only Phase 4 LangGraph sessions are supported."
            )
        
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
        
        # Invoke the conversation graph to get AI response
        try:
            result = await asyncio.to_thread(conversation_graph.invoke, state)
            
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
            logger.error(f"Error invoking conversation graph for session {session_id}: {e}")
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
