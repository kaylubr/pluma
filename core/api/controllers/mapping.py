from core.models import Document, Question
from core.schemas.api import QuestionOut, ReviewerDetail, ReviewerSummary


def question_to_out(question: Question) -> QuestionOut:
    return QuestionOut(
        id=question.id,
        sentence_id=question.sentence_id,
        sentence_text=question.sentence.text,
        text=question.text,
        answer=question.answer,
        reason=question.reason,
        is_valid=question.is_valid,
        discarded=question.discarded,
    )


def document_to_summary(document: Document, question_count: int) -> ReviewerSummary:
    return ReviewerSummary(
        id=document.id,
        filename=document.filename,
        created_at=document.created_at,
        question_count=question_count,
    )


def document_to_detail(document: Document, questions: list[Question]) -> ReviewerDetail:
    return ReviewerDetail(
        id=document.id,
        filename=document.filename,
        created_at=document.created_at,
        questions=[question_to_out(question) for question in questions],
    )
