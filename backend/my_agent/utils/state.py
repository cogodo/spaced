from typing import TypedDict, List, Dict, Optional

class GraphState(TypedDict):
    # The list of study topics the user wants to cover
    topics: List[str]

    # Index of the current topic (0-based)
    current_topic_index: int

    # How many questions have been asked so far for the current topic
    question_count: int

    # A running list of {"question": str, "answer": str} pairs
    history: List[Dict[str, str]]

    # The most recent user input (or None when it's time to ask the first question)
    user_input: Optional[str]

    # The next question to send back to the user (filled by the respond node)
    next_question: Optional[str]

    # Whether we've exhausted all topics/questions and should evaluate
    done: bool

    # Once done=True, the evaluator will fill this mapping: topic -> FSRS score (0–5)
    scores: Optional[Dict[str, int]]

    # Configuration: maximum number of topics to cover (e.g. 3)
    max_topics: int

    # Configuration: maximum questions per topic (e.g. 7)
    max_questions: int
