import os
import json
import random
from typing import Dict

def call_main_llm(state: Dict) -> str:
    """
    Mock implementation: Generates the next active-recall question for the current topic.
    - state["topics"][state["current_topic_index"]] is the string of the current topic.
    - state["history"] is a list of previous {"question":..., "answer":...} for this topic.
    Returns a single question (string).
    """
    current_idx = state["current_topic_index"]
    topic = state["topics"][current_idx]
    history = state["history"]
    question_count = state["question_count"]

    # Mock questions based on topic and question number
    mock_questions = [
        f"What are the key fundamentals you should know about {topic}?",
        f"Can you explain the main concepts related to {topic}?",
        f"What are the practical applications of {topic}?",
        f"How would you describe {topic} to someone new to the field?",
        f"What are the common challenges when working with {topic}?",
        f"What best practices should you follow when using {topic}?",
        f"How does {topic} relate to other technologies or concepts?"
    ]
    
    # Avoid repeating questions by tracking what was asked
    asked_questions = [qa['question'] for qa in history]
    available_questions = [q for q in mock_questions if q not in asked_questions]
    
    if available_questions:
        return available_questions[0]
    else:
        # If we've asked all pre-made questions, generate a generic one
        return f"Question #{question_count}: What else can you tell me about {topic}?"

def call_evaluator_llm(state: Dict) -> Dict[str, int]:
    """
    Mock implementation: Given the full conversation history and the original topic list, 
    assign an FSRS-style score (0–5) to each topic. Return a dict mapping topic -> integer score.
    """
    topics = state["topics"]
    history = state["history"]

    # Mock scoring based on simple heuristics
    scores = {}
    
    for topic in topics:
        # Count how many questions were answered for this topic
        topic_questions = [qa for qa in history if topic.lower() in qa['question'].lower()]
        
        # Simple scoring: more questions answered = higher score, with some randomness
        base_score = min(len(topic_questions), 3)  # Base score from 0-3
        
        # Add some randomness and variation based on answer length
        total_answer_length = sum(len(qa['answer']) for qa in topic_questions)
        if total_answer_length > 100:  # Longer answers get bonus
            base_score += 1
        if total_answer_length > 200:  # Really detailed answers get more bonus
            base_score += 1
            
        # Add small random variation
        variation = random.randint(-1, 1)
        final_score = max(0, min(5, base_score + variation))
        
        scores[topic] = final_score
    
    return scores

# Keep the original functions commented out for when API keys are available
"""
Original OpenAI-powered implementations:

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def get_llm_client() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

def call_main_llm_openai(state: Dict) -> str:
    llm = get_llm_client()
    current_idx = state["current_topic_index"]
    topic = state["topics"][current_idx]
    history = state["history"]

    prompt_lines = [
        f"You are an active-recall study assistant. Your job is to ask EXACTLY ONE question "
        f"to help the user recall details about the topic: \"{topic}\". ",
        f"You should look at the previous Q&A for this topic to avoid repeating questions."
    ]
    if history:
        example_lines = ["Previous Q&A:"]
        for idx, qa in enumerate(history, start=1):
            example_lines.append(f"{idx}. Q: {qa['question']}  A: {qa['answer']}")
        prompt_lines.append("\n".join(example_lines))

    prompt_lines.append(
        "Now produce a single, clear, active-recall question (not multiple questions). "
        "Do NOT answer it yourself; just output the question."
    )
    full_prompt = "\n\n".join(prompt_lines)

    message = HumanMessage(content=full_prompt)
    response = llm.invoke([message])
    question = response.content.strip()
    return question

def call_evaluator_llm_openai(state: Dict) -> Dict[str, int]:
    llm = get_llm_client()
    topics = state["topics"]
    history = state["history"]

    prompt_lines = [
        "You are an evaluator that assigns spaced-repetition (FSRS) scores to topics based on how well the user answered.",
        f"The user wanted to study these topics: {json.dumps(topics)}.",
        "Here is the full Q&A history across all topics (each entry is {\"question\":..., \"answer\":...}):",
        json.dumps(history, indent=2),
        (
            "For each topic in the original list, assign an integer FSRS score from 0 to 5 "
            "(0 = needs major review, 5 = mastered). "
            "Output ONLY a JSON object mapping each topic to its integer score, e.g.:\n"
            "{\"Topic A\": 4, \"Topic B\": 2, \"Topic C\": 5}"
        )
    ]
    full_prompt = "\n\n".join(prompt_lines)

    message = HumanMessage(content=full_prompt)
    response = llm.invoke([message])
    text = response.content.strip()

    try:
        scores = json.loads(text)
        final: Dict[str, int] = {}
        for t in topics:
            val = scores.get(t, 0)
            final[t] = int(val)
        return final
    except Exception as e:
        return {t: 0 for t in topics}
"""
