from datetime import datetime

from pydantic import BaseModel


class QuestionOut(BaseModel):
    id: int
    sentence_id: int
    sentence_text: str
    text: str
    answer: str
    reason: str
    is_valid: bool
    discarded: bool


class ReviewerSummary(BaseModel):
    id: int
    filename: str
    created_at: datetime
    question_count: int


class ReviewerDetail(BaseModel):
    id: int
    filename: str
    created_at: datetime
    questions: list[QuestionOut]


class QuestionDiscard(BaseModel):
    discarded: bool
