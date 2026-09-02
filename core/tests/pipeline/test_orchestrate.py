from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from core.db.session import create_db_engine
from core.models import Base, Document, Question, Sentence
from core.services.orchestrate import process_document
from core.tests.helper import TINY_PDF

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

DUPLICATED_CONTENT = (
    "Waiting for P2 to release R1, the scheduling algorithm decides next.\n"
    "Waiting for P2 to release R1, the scheduling algorithm decides next."
)


@pytest.fixture
def session():
    engine = create_db_engine()
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    s = factory()
    try:
        yield s
    finally:
        s.close()
        engine.dispose()


def _load(filename: str) -> bytes:
    with open(FIXTURES / filename, "rb") as f:
        return f.read()


class TestProcessDocument:
    def test_processes_pdf_keeps_only_scored_sentences(self, session):
        doc_id = process_document(session, "lesson.pdf", _load("lesson.pdf"))
        session.commit()
        doc = session.get(Document, doc_id)
        assert doc.filename == "lesson.pdf"

        sentences = session.query(Sentence).filter_by(document_id=doc_id).all()
        assert len(sentences) > 0
        assert all(s.worth_question is True for s in sentences)

    def test_processes_pdf_stores_valid_and_invalid_questions(self, session):
        doc_id = process_document(session, "lesson.pdf", _load("lesson.pdf"))
        session.commit()
        questions = (
            session.query(Question)
            .join(Sentence, Question.sentence_id == Sentence.id)
            .filter(Sentence.document_id == doc_id)
            .all()
        )
        assert len(questions) >= 2
        assert any(q.is_valid for q in questions)
        assert any(not q.is_valid for q in questions)

    def test_processes_pptx_stores_invalid_too_short_questions(self, session):
        doc_id = process_document(session, "slides.pptx", _load("slides.pptx"))
        session.commit()
        questions = (
            session.query(Question)
            .join(Sentence, Question.sentence_id == Sentence.id)
            .filter(Sentence.document_id == doc_id)
            .all()
        )
        assert len(questions) >= 3
        for q in questions:
            assert q.is_valid is False
            assert "too_short" in q.validation_reasons.split(",")

    def test_zero_question_document_still_created(self, session):
        doc_id = process_document(session, "empty.pdf", TINY_PDF)
        session.commit()
        doc = session.get(Document, doc_id)
        assert doc is not None
        assert session.query(Sentence).filter_by(document_id=doc_id).count() == 0
        assert (
            session.query(Question)
            .join(Sentence, Question.sentence_id == Sentence.id)
            .filter(Sentence.document_id == doc_id)
            .count()
            == 0
        )

    def test_unsupported_extension_raises(self, session):
        with pytest.raises(ValueError, match="Unsupported file type"):
            process_document(session, "lesson.docx", b"bytes")

    def test_does_not_commit(self, session):
        process_document(session, "lesson.pdf", _load("lesson.pdf"))
        session.rollback()
        assert session.query(Document).count() == 0
        assert session.query(Sentence).count() == 0
        assert session.query(Question).count() == 0

    def test_duplicate_answers_deduped_in_document(self, session, monkeypatch):
        monkeypatch.setattr(
            "core.services.orchestrate.extract_text",
            lambda filename, contents: DUPLICATED_CONTENT,
        )
        doc_id = process_document(session, "lesson.pdf", b"ignored")
        session.commit()
        sentences = session.query(Sentence).filter_by(document_id=doc_id).all()
        assert len(sentences) == 2
        questions = (
            session.query(Question)
            .join(Sentence, Question.sentence_id == Sentence.id)
            .filter(Sentence.document_id == doc_id)
            .all()
        )
        answers = [q.answer for q in questions]
        assert answers == ["scheduling algorithm", "scheduling algorithm"]
        assert sum(1 for q in questions if q.discarded) == 1
        active = [q for q in questions if q.is_valid and not q.discarded]
        assert len(active) == 1
        assert active[0].answer == "scheduling algorithm"
