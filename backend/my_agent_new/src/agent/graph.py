"""
Spaced Repetition Learning Agent LangGraph
Intelligent learning companion with adaptive conversation and spaced repetition features
"""

from __future__ import annotations

from typing import Dict, Any
import logging

from langgraph.graph import StateGraph, END

from agent.state import GraphState
from agent.nodes import (
    review_questions_node, 
    conversation_node, 
    evaluate_topic_node
    )
from agent.tools import decide_topic_action, decide_after_evaluation

# Configure logging
logger = logging.getLogger(__name__)

#TODO: this is the only conditional edge I think I need (for now) - 
# just gotta make a proper routing function 
def route_from_conversation(state: GraphState) -> str:
    """Route from conversation_node based on current state"""
    return NotImplemented

#TODO: Add a tools node for each of the nodes that need various tools to access
def build_learning_graph() -> StateGraph:
    """
    Build the main learning graph 
    """
    graph = StateGraph(state_schema=GraphState)

    # Add all nodes
    graph.add_node("get_questions", review_questions_node)
    graph.add_node("conversation", conversation_node)
    graph.add_node("evaluate_topic", evaluate_topic_node)
    graph.add_node("complete_session", TODO)

    # Set entry point
    graph.set_entry_point("get_questions")
    
    graph.add_edge("get_questions", "conversation")
    
    # Define conditional edges for conversation flow
    graph.add_conditional_edges(
        "conversation",
        route_from_conversation,
        {
            "continue_topic": "conversation",      # Loop back for more conversation
            "evaluate_topic": "evaluate_topic",   # Move to evaluation
            "end_session": "complete_session",    # End the session
            "error": "complete_session"           # Handle errors by ending
        }
    )
    graph.add_edge("evaluate_topic", "conversation")     # Move to next topic
    # complete_session is terminal
    graph.add_edge("complete_session", END)

    return graph

graph = build_learning_graph().compile(
    name="Spaced Repetition Learning Agent",
    interrupt_after=["conversation"]
)
