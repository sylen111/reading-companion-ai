from typing import TypedDict, Optional

class ReadingState(TypedDict):
    selected_text: str
    annotation_type: str
    explanation: str

    question: str
    chat_history: list

    category_fail_count: int
    item_fail_count: int

    explanation_depth: str
    need_quiz: bool

    quiz: Optional[str]
    answer: Optional[str]