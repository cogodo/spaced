from typing import Dict, Any
from my_agent.utils.state import GraphState
from my_agent.utils.tools import call_main_llm, call_evaluator_llm

def respond_node(state: GraphState) -> Dict[str, Any]:
    """
    If state['user_input'] is None, this is the very first call:
      - Initialize question_count to 1
      - Generate the first question for topic at index 0
    Otherwise:
      - Record the user's answer (state['user_input']) into history for the *previous* question
      - If we haven't hit max_questions for this topic, generate the next question
      - If we have hit max_questions for this topic:
          • If there are more topics left, advance topic and generate question #1 for next topic
          • Otherwise, set state['done'] = True
    Always clear state['user_input'] after consuming it.
    Returns a dict that may contain:
      - "next_question": str
      - updated "question_count" (int)
      - updated "current_topic_index" (int)
      - updated "history" (list)
      - updated "done" (bool)
    """
    # Pull config
    max_q = state["max_questions"]
    max_t = state["max_topics"]
    topics = state["topics"]

    # If this is the first ever call (user_input == None), we just ask the first question
    if state["user_input"] is None:
        # Initialize counters
        state["current_topic_index"] = 0
        state["question_count"] = 1
        state["done"] = False
        # Start fresh history
        state["history"] = []
        # Ask the first question
        question = call_main_llm(state)
        state["next_question"] = question
        return {
            "next_question": question,
            "current_topic_index": state["current_topic_index"],
            "question_count": state["question_count"],
            "history": state["history"],
            "done": state["done"]
        }

    # Otherwise, user_input is an answer to the *last* question we sent
    last_answer = state["user_input"]
    last_question = state.get("next_question", "")
    # Record that Q&A pair in history
    state["history"].append({"question": last_question, "answer": last_answer})

    # Clear the user_input for the next run
    state["user_input"] = None

    # Check if we've hit the per-topic question limit
    if state["question_count"] < max_q:
        # Ask another question on the same topic
        state["question_count"] += 1
        question = call_main_llm(state)
        state["next_question"] = question
        return {
            "next_question": question,
            "question_count": state["question_count"],
            "history": state["history"]
        }
    else:
        # We’ve already asked max_q questions for this topic
        # See if there’s another topic we can move to
        if state["current_topic_index"] + 1 < min(len(topics), max_t):
            state["current_topic_index"] += 1
            state["question_count"] = 1
            # Generate the first question for the next topic
            question = call_main_llm(state)
            state["next_question"] = question
            return {
                "next_question": question,
                "current_topic_index": state["current_topic_index"],
                "question_count": state["question_count"],
                "history": state["history"]
            }
        else:
            # No more topics to cover: we are done
            state["done"] = True
            state["next_question"] = None
            return {
                "done": True,
                "history": state["history"]
            }

def evaluate_node(state: GraphState) -> Dict[str, Any]:
    """
    If state['done'] is True, call the evaluator LLM to assign FSRS scores.
    Returns {"scores": {...}} only when done==True; otherwise returns {}.
    """
    if state["done"]:
        scores = call_evaluator_llm(state)
        state["scores"] = scores
        return {"scores": scores}
    return {}
