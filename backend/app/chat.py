from enum import Enum

from pydantic import BaseModel, Field

from app.annotation import Annotation


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    annotation: Annotation
    question: str
    chat_history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str