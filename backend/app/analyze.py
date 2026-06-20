from pydantic import BaseModel, Field

from app.annotation import Annotation

class AnalyzeRequest(BaseModel):
    article: str = Field(
        min_length=50,
        max_length=10000
    )

class AnalyzeResponse(BaseModel):
    annotations: list[Annotation]