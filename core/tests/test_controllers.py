from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from core.api.controllers import questions as question_controller
from core.api.controllers import reviewers as reviewer_controller
from core.db.session import create_db_engine
from core.models import Base
from core.schemas.api import QuestionOut, ReviewerDetail, ReviewerSummary
from core.services import store
from core.tests.helper import TINY_PDF, make_cloze, make_scored, make_validation

FIXTURES = Path(__file__).resolve().parent / "fixtures"


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


def _seed_reviewer(session):
    doc_id = store.store_document(session, "lesson.pdf")
    first_id = store.store_sentences(
        session,
        doc_id,
        [make_scored("Cells are the basic unit of life.", True, "factual_claim")],
    )[0]
    second_id = store.store_sentences(
        session,
        doc_id,
        [make_scored("Both organelles have their own DNA", True, "factual_claim")],
    )[0]
    valid_id = store.store_question(
        session,
        first_id,
        make_cloze("Cells are the basic unit of life.", "_____ are the basic unit of life.", "Cells"),
        make_validation(True),
    )
    store.store_question(
        session,
        first_id,
        make_cloze("Cells divide.", "_____ divide.", "Cells"),
        make_validation(False, ["too_short"]),
    )
    discarded_id = store.store_question(
        session,
        second_id,
        make_cloze("Both organelles have their own DNA", "Both _____ have their own DNA", "organelles"),
        make_validation(True),
    )
    store.set_question_discarded(session, discarded_id, True)
    session.commit()
    return doc_id, valid_id, discarded_id


class TestCreateReviewer:
    def test_creates_reviewer_with_valid_questions(self, session):
        with open(FIXTURES / "lesson.pdf", "rb") as f:
            contents = f.read()
        result = reviewer_controller.create_reviewer(session, "lesson.pdf", contents)
        assert isinstance(result, ReviewerDetail)
        assert result.filename == "lesson.pdf"
        assert result.questions
        for q in result.questions:
            assert isinstance(q, QuestionOut)
            assert q.is_valid is True
            assert q.discarded is False
            assert q.sentence_text

    def test_zero_valid_questions_yields_empty_deck(self, session):
        result = reviewer_controller.create_reviewer(session, "empty.pdf", TINY_PDF)
        assert isinstance(result, ReviewerDetail)
        assert result.questions == []


class TestListReviewers:
    def test_summaries_count_only_servable_questions(self, session):
        _seed_reviewer(session)
        summaries = reviewer_controller.list_reviewers(session)
        assert len(summaries) == 1
        summary = summaries[0]
        assert isinstance(summary, ReviewerSummary)
        assert summary.filename == "lesson.pdf"
        assert summary.question_count == 1

    def test_empty_database_returns_empty_list(self, session):
        assert reviewer_controller.list_reviewers(session) == []


class TestGetReviewerQuestions:
    def test_returns_only_valid_and_non_discarded_in_document_order(self, session):
        doc_id, valid_id, discarded_id = _seed_reviewer(session)
        result = reviewer_controller.get_reviewer_questions(session, doc_id)
        assert result is not None
        assert [q.id for q in result] == [valid_id]
        assert result[0].answer == "Cells"

    def test_unknown_reviewer_returns_none(self, session):
        assert reviewer_controller.get_reviewer_questions(session, 9999) is None


class TestUpdateQuestionDiscard:
    def test_discard_and_restore(self, session):
        doc_id, valid_id, _ = _seed_reviewer(session)
        updated = question_controller.update_question_discard(session, valid_id, True)
        assert updated is not None
        assert updated.discarded is True
        assert reviewer_controller.get_reviewer_questions(session, doc_id) == []

        restored = question_controller.update_question_discard(session, valid_id, False)
        assert restored is not None
        assert restored.discarded is False
        questions = reviewer_controller.get_reviewer_questions(session, doc_id)
        assert [q.id for q in questions] == [valid_id]

    def test_unknown_question_returns_none(self, session):
        assert question_controller.update_question_discard(session, 9999, True) is None
