"""
Spaced Repetition Learning Agent LangGraph
Intelligent learning companion with adaptive conversation and spaced repetition features
"""

from __future__ import annotations

from typing import Dict, Any
import logging
from datetime import datetime

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END

from agent.state import GraphState
from agent.nodes import (
    session_initialization_node, 
    conversation_node, 
    evaluate_topic_node, 
    complete_session_with_topic_scores
)
from agent.tools import decide_topic_action, decide_after_evaluation

# Configure logging
logger = logging.getLogger(__name__)


def update_state_with_user_input(state: GraphState, user_input: str) -> GraphState:
    """
    Utility function to properly update state with user input during interrupts.
    This ensures the input is ready for the conversation node when resuming.
    """
    # Update the state with user input
    updated_state = state.copy()
    updated_state["user_input"] = user_input.strip()
    
    # Increment message count for user input tracking
    updated_state["message_count"] = updated_state.get("message_count", 0) + 1
    
    logger.info(f"State updated with user input: {len(user_input)} characters")
    return updated_state


def clear_processed_user_input(state: GraphState) -> GraphState:
    """
    Clear user input after it's been processed to prevent reprocessing.
    Call this after the conversation node processes the input.
    """
    updated_state = state.copy()
    updated_state["user_input"] = None
    return updated_state


class InterruptedGraphManager:
    """
    Helper class to manage interrupted graphs and user input handling.
    Makes it easy to handle the interrupt -> user input -> resume cycle.
    """
    
    @staticmethod
    def resume_with_user_input(graph, interrupted_state: GraphState, user_input: str) -> dict:
        """
        Resume an interrupted graph with user input.
        
        Args:
            graph: The compiled LangGraph
            interrupted_state: The state when the graph was interrupted
            user_input: The user's response/input
            
        Returns:
            The result of resuming the graph with the user input
        """
        try:
            # Update state with user input
            updated_state = update_state_with_user_input(interrupted_state, user_input)
            
            # Resume graph execution with updated state
            result = graph.invoke(updated_state)
            
            logger.info("Graph successfully resumed with user input")
            return result
            
        except Exception as e:
            logger.error(f"Error resuming graph with user input: {e}")
            raise
    
    @staticmethod
    def is_waiting_for_input(state: GraphState) -> bool:
        """
        Check if the state indicates the system is waiting for user input.
        This happens after an interrupt when user_input is None.
        """
        return (
            state.get("user_input") is None and 
            not state.get("session_complete", False) and
            state.get("next_question") is not None
        )
    
    @staticmethod
    def get_last_ai_message(state: GraphState) -> str:
        """
        Get the last AI message from the state, useful for displaying to user.
        """
        return state.get("next_question", "I'm ready for your response!")
    
    @staticmethod
    def create_input_prompt(state: GraphState) -> str:
        """
        Create a helpful input prompt for the user based on current state.
        """
        current_topic = state.get("current_topic")
        if current_topic:
            return f"Continue discussing {current_topic}:"
        else:
            return "Your response:"


def handle_langsmith_input(state_or_string):
    """
    LangSmith-friendly wrapper that can handle both full state and simple string inputs.
    This makes testing in LangSmith much easier - you can just type responses as strings.
    Now supports the standard messages key for chat interfaces.
    """
    # If it's a string, treat it as user input for an interrupted session
    if isinstance(state_or_string, str):
        # For LangSmith: create a minimal state with the user input in messages format
        return {
            "messages": [
                {
                    "type": "human",
                    "content": state_or_string.strip(),
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "user_input": state_or_string.strip(),  # Keep for backward compatibility
            "message_count": 1,
            "topics": ["General Topic"],  # Default for testing  
            "session_type": "custom_topics",
            "current_topic": "General Topic"
        }
    
    # If it's already a dict/state, return as-is
    return state_or_string


def create_langsmith_friendly_graph():
    """
    Create a version of the graph that's easier to test in LangSmith.
    This version can accept simple strings as input during interrupts.
    """
    from langgraph.graph import StateGraph, END
    
    # Wrapper node that handles string inputs
    def langsmith_input_handler(state):
        """Handle both string inputs and state objects for LangSmith compatibility"""
        processed_state = handle_langsmith_input(state)
        return processed_state
    
    # Create graph with input handler
    graph = StateGraph(state_schema=GraphState)
    
    # Add input handler as first node
    graph.add_node("input_handler", langsmith_input_handler)
    graph.add_node("session_init", session_initialization_node)  
    graph.add_node("conversation", conversation_node)
    graph.add_node("evaluate_topic", evaluate_topic_node)
    graph.add_node("complete_session", complete_session_with_topic_scores)

    # Set entry point to input handler
    graph.set_entry_point("input_handler")
    
    # Route from input handler
    graph.add_conditional_edges(
        "input_handler",
        lambda state: "session_init" if not state.get("user_input") else "conversation",
        {
            "session_init": "session_init",
            "conversation": "conversation"
        }
    )
    
    # Standard edges
    graph.add_edge("session_init", "conversation")
    
    # Conditional edges for conversation flow
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

    # Conditional edges for evaluation flow
    graph.add_conditional_edges(
        "evaluate_topic",
        route_from_evaluation,
        {
            "next_topic": "conversation",
            "end_session": "complete_session",
        }
    )

    # Terminal edge
    graph.add_edge("complete_session", END)
    
    return graph.compile(
        name="LangSmith Friendly Learning Agent",
        interrupt_after=["conversation"]
    )


def route_from_conversation(state: GraphState) -> str:
    """Route from conversation_node based on current state"""
    # Check for legacy patterns (security)
    user_input = state.get("user_input", "")
    if user_input and any(legacy_term in user_input.lower() for legacy_term in ['use_legacy', 'old_system', 'legacy_mode']):
        logger.error("Legacy system usage attempted - rejecting")
        return "error"
    
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
    """Route from evaluate_topic_node based on evaluation results"""
    try:
        decision = decide_after_evaluation(state)
        logger.info(f"Evaluation routing decision: {decision}")
        
        # Map decisions to valid graph edges  
        if decision == "next_topic":
            return "next_topic"
        elif decision == "end_session":
            return "end_session"
        else:
            logger.warning(f"Unknown evaluation decision: {decision}, defaulting to end_session")
            return "end_session"
            
    except Exception as e:
        logger.error(f"Error in evaluation routing: {e}")
        return "end_session"


def build_learning_graph() -> StateGraph:
    """
    Build the main learning graph with proper LangGraph structure
    """
    # Create the StateGraph with our custom state schema
    graph = StateGraph(state_schema=GraphState)

    # Add all nodes
    graph.add_node("session_init", session_initialization_node)
    graph.add_node("conversation", conversation_node)
    graph.add_node("evaluate_topic", evaluate_topic_node)
    graph.add_node("complete_session", complete_session_with_topic_scores)

    # Set entry point
    graph.set_entry_point("session_init")
    
    # Define edges from session initialization
    graph.add_edge("session_init", "conversation")
    
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

    # Define conditional edges for evaluation flow
    graph.add_conditional_edges(
        "evaluate_topic", 
        route_from_evaluation,
        {
            "next_topic": "conversation",         # Move to next topic
            "end_session": "complete_session",   # End the session
        }
    )

    # complete_session is terminal
    graph.add_edge("complete_session", END)

    return graph


def build_conversation_graph() -> StateGraph:
    """
    Build graph specifically for conversation flow (answer processing)
    This is used when processing user answers during a session
    """
    graph = StateGraph(state_schema=GraphState)
    
    # Add conversation nodes only
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
        }
    )

    # complete_session is terminal
    graph.add_edge("complete_session", END)
    
    return graph


# The main graph that LangGraph Server expects
# This is what langgraph.json points to: "./src/agent/graph.py:graph"
graph = build_learning_graph().compile(
    name="Spaced Repetition Learning Agent",
    interrupt_after=["conversation"]
)

# Additional graphs for different use cases
conversation_graph = build_conversation_graph().compile(
    name="Conversation Flow",
    interrupt_after=["conversation"]
)
init_graph = StateGraph(state_schema=GraphState).add_node("session_init", session_initialization_node).set_entry_point("session_init").add_edge("session_init", END).compile(name="Session Initialization")

# LangSmith-friendly graph for easy testing
langsmith_graph = create_langsmith_friendly_graph()

# Simple messages-only chat graph
simple_chat_graph = create_simple_chat_graph()


# Export the helper manager for easy import
__all__ = ["graph", "conversation_graph", "init_graph", "langsmith_graph", "simple_chat_graph", "InterruptedGraphManager", "update_state_with_user_input"]


"""
USAGE EXAMPLE FOR INTERRUPTED GRAPHS WITH USER INPUT:

# Start a session
initial_state = {
    "session_id": "example_session",
    "topics": ["Python", "Machine Learning"],
    "session_type": "custom_topics"
}

# Run until first interrupt (after conversation node)
result = graph.invoke(initial_state)

# Check if waiting for input
if InterruptedGraphManager.is_waiting_for_input(result):
    # Display AI's message to user
    ai_message = InterruptedGraphManager.get_last_ai_message(result)
    print(f"AI: {ai_message}")
    
    # Get user input (however your UI does this)
    user_response = "I think Python is a programming language used for many things..."
    
    # Resume with user input
    next_result = InterruptedGraphManager.resume_with_user_input(
        graph=graph,
        interrupted_state=result,
        user_input=user_response
    )
    
    # Continue this pattern until session is complete
    while not next_result.get("session_complete", False):
        if InterruptedGraphManager.is_waiting_for_input(next_result):
            ai_message = InterruptedGraphManager.get_last_ai_message(next_result)
            print(f"AI: {ai_message}")
            
            # Get next user input
            user_response = input("You: ")
            
            # Resume again
            next_result = InterruptedGraphManager.resume_with_user_input(
                graph=graph,
                interrupted_state=next_result,
                user_input=user_response
            )
        else:
            break
    
    print("Session completed!")
    print(next_result.get("completion_message", "Thanks for learning!"))

ARCHITECTURE SUMMARY:
1. Graph executes conversation node -> generates AI response
2. interrupt_after=["conversation"] pauses execution
3. Use InterruptedGraphManager.resume_with_user_input() to continue
4. User input is automatically stored in state.user_input
5. When conversation node resumes, it processes the user_input
6. User input is recorded in conversation_history and then cleared
7. Process repeats until session is complete

===================================================================
LANGSMITH TESTING GUIDE:
===================================================================

For easy testing in LangSmith, use the "langsmith_testing" graph:

1. INITIAL SESSION START:
   Input: {}
   → This will start a new session with default topics

2. FIRST INTERRUPT - AI asks a question:
   → Graph pauses after conversation node
   → You'll see the AI's question in the output

3. RESUME WITH SIMPLE TEXT:
   Input: "I think Python is a great language for beginners"
   → Just type your response as a plain string!
   → No need for JSON formatting

4. CONTINUE THE CONVERSATION:
   → Keep providing simple text responses
   → The graph handles all the state management internally

LANGSMITH WORKFLOW:
┌─────────────────────────────────────────────────────┐
│ 1. Start: Input {} (empty object)                  │
│    → AI generates welcome + first question         │
│    → Graph interrupts, waiting for response        │
├─────────────────────────────────────────────────────┤
│ 2. Respond: Input "Your answer here"               │
│    → AI processes your response                     │
│    → AI asks follow-up question                     │
│    → Graph interrupts again                         │
├─────────────────────────────────────────────────────┤
│ 3. Continue: Input "Another response"              │
│    → Conversation continues...                      │
│    → Until topic is complete or session ends       │
└─────────────────────────────────────────────────────┘

AVAILABLE GRAPHS IN LANGSMITH:
- "main": Full production graph (requires complete state objects)
- "langsmith_testing": Simplified for testing (accepts plain strings)
- "conversation": For ongoing conversations only
- "init": Just the initialization node

TIP: Use "langsmith_testing" for the easiest experience!
"""

def create_simple_chat_graph():
    """
    Create a simple chat graph that uses only the messages key.
    Perfect for LangSmith testing with standard chat interface.
    """
    from langgraph.graph import StateGraph, END
    
    def simple_chat_node(state):
        """Simple chat node that works purely with messages"""
        messages = state.get("messages", [])
        
        # If no messages, start a new session
        if not messages:
            opening = "Hello! I'm your learning companion. What would you like to learn about today?"
            return {
                "messages": [
                    {
                        "type": "ai",
                        "content": opening,
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
        
        # Get the last human message
        last_human_message = None
        for msg in reversed(messages):
            if msg.get("type") == "human":
                last_human_message = msg.get("content", "")
                break
        
        if not last_human_message:
            return {"messages": messages}
        
        # Generate AI response (simplified for demonstration)
        ai_response = f"That's interesting! You said: '{last_human_message}'. Tell me more about what you'd like to explore regarding this topic."
        
        # Add AI response to messages
        new_messages = messages + [
            {
                "type": "ai", 
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        return {"messages": new_messages}
    
    # Create simple graph
    graph = StateGraph(state_schema=GraphState)
    graph.add_node("chat", simple_chat_node)
    graph.set_entry_point("chat")
    graph.add_edge("chat", END)
    
    return graph.compile(
        name="Simple Chat Agent",
        interrupt_after=["chat"]
    )
