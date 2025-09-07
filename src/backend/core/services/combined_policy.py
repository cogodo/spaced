from core.models.llm_outputs import NextAction


def enforce_after_hint_cap(score: int, after_hint: bool) -> int:
    if after_hint and score > 4:
        return 4
    return score


def decide_next_action(score: int, user_requested_end: bool = False) -> NextAction:
    if user_requested_end:
        return NextAction.END_CHAT
    if score >= 4:
        return NextAction.MOVE_TO_NEXT_QUESTION
    return NextAction.AWAIT_CLARIFICATION
