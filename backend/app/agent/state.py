from typing import TypedDict, Optional

class ReadingState(TypedDict):
    book_id: str
    
    selected_text: str
    annotation_type: str
    explanation: str

    use_annotation: bool

    question: str
    chat_history: list

    category_fail_count: int
    item_fail_count: int

    explanation_depth: str
    need_quiz: bool

    need_rag: bool
    rag_context: str

    quiz: Optional[str]
    answer: Optional[str]