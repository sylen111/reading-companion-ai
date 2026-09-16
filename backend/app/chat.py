from enum import Enum
from pydantic import BaseModel, Field
from app.annotation import Annotation


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    annotation: Annotation | None = None
    question: str
    chat_history: list[ChatMessage] = Field(default_factory=list)
    book_id: str
    use_annotation: bool = False


class ChatResponse(BaseModel):
    answer: str