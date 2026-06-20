from enum import Enum

from pydantic import BaseModel, Field


class AnnotationType(str, Enum):
    IDIOM = "idiom"
    CHUNK = "chunk"


class Annotation(BaseModel):
    id: str = Field(
        description="Unique annotation identifier"
    )

    text: str = Field(
        description="Original text span"
    )

    type: AnnotationType

    start: int = Field(
        ge=0,
        description="Start character index"
    )

    end: int = Field(
        gt=0,
        description="End character index"
    )

    explanation: str = Field(
        description="User-friendly explanation"
    )