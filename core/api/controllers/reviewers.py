from sqlalchemy.orm import Session

from core.api.controllers import mapping
from core.schemas.api import QuestionOut, ReviewerDetail, ReviewerSummary
from core.services import orchestrate, store


def create_reviewer(session: Session, filename: str, contents: bytes) -> ReviewerDetail:
    document_id = orchestrate.process_document(session, filename, contents)
    document = store.get_document(session, document_id)
    questions = store.list_valid_questions(session, document_id)
    return mapping.document_to_detail(document, questions)


def list_reviewers(session: Session) -> list[ReviewerSummary]:
    documents = store.list_documents(session)
    return [
        mapping.document_to_summary(document, store.count_valid_questions(session, document.id))
        for document in documents
    ]


def get_reviewer_questions(session: Session, reviewer_id: int) -> list[QuestionOut] | None:
    if store.get_document(session, reviewer_id) is None:
        return None
    questions = store.list_valid_questions(session, reviewer_id)
    return [mapping.question_to_out(question) for question in questions]
