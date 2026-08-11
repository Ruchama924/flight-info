from __future__ import annotations

from pydantic import BaseModel, Field


class AskAdvisorRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class AskAdvisorResponse(BaseModel):
    answer: str
    topics_used: list[str]
    question: str
