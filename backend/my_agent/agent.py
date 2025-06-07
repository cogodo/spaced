import uuid
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import logging

from langgraph.graph import StateGraph

from my_agent.utils.state import GraphState
from my_agent.utils.nodes import respond_node, evaluate_node

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_graph():
    """
    Build a LangGraph with two nodes:
      1. respond_node: asks/records Q&A
      2. evaluate_node: computes FSRS scores once done=True
    """
    # NOTE: We must pass state_schema=GraphState here to avoid a ValueError
    graph = StateGraph(state_schema=GraphState)

    # Add nodes directly without ToolNode wrapper
    graph.add_node("respond_node", respond_node)
    graph.add_node("evaluate_node", evaluate_node)

    # Add edges to connect the nodes
    graph.add_edge("respond_node", "evaluate_node")
    
    # Set the entry point
    graph.set_entry_point("respond_node")
    
    # Compile the graph to make it executable
    return graph.compile()


compiled_graph = build_graph()

# In‐memory store of session_id -> GraphState
SESSIONS: Dict[str, GraphState] = {}


class StartPayload(BaseModel):
    topics: list[str]
    max_topics: int = 3
    max_questions: int = 7


class AnswerPayload(BaseModel):
    session_id: str
    user_input: str


# Get environment variables
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app = FastAPI(
    title="Spaced Learning API",
    description="AI-powered spaced repetition learning API",
    version="1.0.0",
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


@app.post("/start_session")
async def start_session(payload: StartPayload):
    """Start a new learning session"""
    try:
        logger.info(f"Starting session with topics: {payload.topics}")
        
        # Initialize a fresh GraphState
        state: GraphState = {
            "topics": payload.topics,
            "current_topic_index": 0,
            "question_count": 0,
            "history": [],
            "user_input": None,
            "next_question": None,
            "done": False,
            "scores": None,
            "max_topics": payload.max_topics,
            "max_questions": payload.max_questions
        }

        # Create and store a new session ID
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = state

        # Run the graph one step to get the first question
        updated = compiled_graph.invoke(state)
        SESSIONS[session_id] = updated

        logger.info(f"Session {session_id} started successfully")
        return {"session_id": session_id, "next_question": updated["next_question"]}
    
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")


@app.post("/answer")
async def answer_question(payload: AnswerPayload):
    """Submit an answer to continue the learning session"""
    try:
        session_id = payload.session_id
        if session_id not in SESSIONS:
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")

        state = SESSIONS[session_id]
        state["user_input"] = payload.user_input

        logger.info(f"Processing answer for session {session_id}")
        updated = compiled_graph.invoke(state)
        SESSIONS[session_id] = updated

        if updated["done"]:
            logger.info(f"Session {session_id} completed")
            return {"scores": updated.get("scores", {})}
        else:
            return {"next_question": updated.get("next_question", "")}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing answer: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("my_agent.agent:app", host=HOST, port=PORT, reload=False)
