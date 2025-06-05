import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

from langgraph.graph import StateGraph

from my_agent.utils.state import GraphState
from my_agent.utils.nodes import respond_node, evaluate_node

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()


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


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/start_session")
async def start_session(payload: StartPayload):
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

    return {"session_id": session_id, "next_question": updated["next_question"]}


@app.post("/answer")
async def answer_question(payload: AnswerPayload):
    session_id = payload.session_id
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    state = SESSIONS[session_id]
    state["user_input"] = payload.user_input

    updated = compiled_graph.invoke(state)
    SESSIONS[session_id] = updated

    if updated["done"]:
        return {"scores": updated.get("scores", {})}
    else:
        return {"next_question": updated.get("next_question", "")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("my_agent.agent:app", host="0.0.0.0", port=8000, reload=True)
