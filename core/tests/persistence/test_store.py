from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from core.models import Base, Document, Question, Sentence
from core.db.session import create_db_engine
from core.services.generate import generate_cloze
from core.services.score import score_sentence
from core.services.store import (
    store_document,
    store_question,
    store_questions,
    store_sentence,
    store_sentences,
)
from core.services.validate import validate_question
from core.tests.helper import make_analyzed, make_cloze, make_scored, make_validation

REPO_ROOT = Path(__file__).resolve().parents[3]


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


def _cloze(sentence="Cells are the basic unit of life.", text="_____ are the basic unit of life.", answer="Cells"):
    return make_cloze(sentence, text, answer)


def _stored_sentence(session, document_id, text="Cells are the basic unit of life."):
    return store_sentences(
        session,
        document_id,
        [make_scored(text, True, "factual_claim")],
    )[0]


class TestSchema:
    def test_create_all_creates_tables(self, session):
        result = session.execute(
            sa.text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = {row[0] for row in result}
        assert {"documents", "sentences", "questions"} <= tables


class TestStoreDocument:
    def test_store_document(self, session):
        doc_id = store_document(session, "lesson.pdf")
        session.commit()
        doc = session.get(Document, doc_id)
        assert doc.filename == "lesson.pdf"
        assert doc.created_at is not None

    def test_store_document_returns_distinct_ids(self, session):
        first = store_document(session, "lesson.pdf")
        second = store_document(session, "slides.pptx")
        assert first != second


class TestStoreSentences:
    def test_store_sentences_persists_position_and_fields(self, session):
        doc_id = store_document(session, "lesson.pdf")
        kept = [
            make_scored("Mitochondria produce ATP.", True, "named_entity"),
            make_scored("Ribosomes synthesize proteins.", True, "factual_claim"),
        ]
        ids = store_sentences(session, doc_id, kept)
        session.commit()
        rows = session.query(Sentence).order_by(Sentence.position).all()
        assert len(ids) == 2
        assert [r.position for r in rows] == [0, 1]
        assert [r.text for r in rows] == [
            "Mitochondria produce ATP.",
            "Ribosomes synthesize proteins.",
        ]
        assert [r.worth_question for r in rows] == [True, True]
        assert [r.score_reason for r in rows] == ["named_entity", "factual_claim"]

    def test_persists_supplied_sentences_without_filtering(self, session):
        doc_id = store_document(session, "lesson.pdf")
        mixed = [
            make_scored("ATP", False, "too_short"),
            make_scored("Cells are the basic unit of life.", True, "factual_claim"),
            make_scored("Key organelles:", False, "no_verb"),
        ]
        ids = store_sentences(session, doc_id, mixed)
        session.commit()
        rows = session.query(Sentence).order_by(Sentence.position).all()
        assert len(ids) == 3
        assert [r.position for r in rows] == [0, 1, 2]
        assert [r.worth_question for r in rows] == [False, True, False]
        assert [r.text for r in rows] == [
            "ATP",
            "Cells are the basic unit of life.",
            "Key organelles:",
        ]

    def test_empty_sentences_batch(self, session):
        assert store_sentences(session, 1, []) == []


class TestStoreQuestions:
    def test_store_question_persists_all_fields(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        q_id = store_question(
            session,
            sent_id,
            _cloze(),
            make_validation(False, ["too_short", "ambiguous_blank"]),
        )
        session.commit()
        q = session.get(Question, q_id)
        assert q.text == "_____ are the basic unit of life."
        assert q.answer == "Cells"
        assert q.reason == "noun"
        assert q.is_valid is False
        assert q.validation_reasons == "too_short,ambiguous_blank"
        assert q.discarded is False
        assert q.sentence_id == sent_id

    def test_store_questions_batch_returns_ids_in_order(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        items = [
            (sent_id, _cloze(), make_validation(True)),
            (
                sent_id,
                make_cloze("Cells divide.", "_____ divide.", "Cells"),
                make_validation(False, ["too_short"]),
            ),
        ]
        ids = store_questions(session, items)
        session.commit()
        questions = session.query(Question).order_by(Question.id).all()
        assert len(ids) == 2
        assert len(questions) == 2
        assert [q.id for q in questions] == ids
        assert questions[0].validation_reasons == ""
        assert questions[1].validation_reasons == "too_short"

    def test_empty_questions_batch(self, session):
        assert store_questions(session, []) == []


class TestRelationships:
    def test_document_sentence_question_relationships(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        store_questions(session, [(sent_id, _cloze(), make_validation(True))])
        session.commit()
        doc = session.get(Document, doc_id)
        assert len(doc.sentences) == 1
        sent = doc.sentences[0]
        assert sent.document.filename == "lesson.pdf"
        assert len(sent.questions) == 1
        assert sent.questions[0].answer == "Cells"

    def test_delete_document_cascades_to_sentences_and_questions(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        store_questions(session, [(sent_id, _cloze(), make_validation(True))])
        session.commit()
        session.delete(session.get(Document, doc_id))
        session.commit()
        assert session.query(Sentence).count() == 0
        assert session.query(Question).count() == 0

    def test_delete_sentence_cascades_to_questions(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        store_questions(session, [(sent_id, _cloze(), make_validation(True))])
        session.commit()
        session.delete(session.get(Sentence, sent_id))
        session.commit()
        assert session.query(Question).count() == 0
        assert session.query(Sentence).count() == 0


class TestForeignKeyEnforcement:
    def test_orphan_question_raises_integrity_error(self, session):
        with pytest.raises(IntegrityError):
            store_question(session, 999999, _cloze(), make_validation(True))
        session.rollback()

    def test_orphan_sentence_raises_integrity_error(self, session):
        with pytest.raises(IntegrityError):
            store_sentence(
                session,
                999999,
                0,
                make_scored("Cells divide.", True, "factual_claim"),
            )
        session.rollback()


class TestValidationReasonSerialization:
    def test_valid_question_stores_empty_reasons(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        q_id = store_question(session, sent_id, _cloze(), make_validation(True))
        session.commit()
        assert session.get(Question, q_id).validation_reasons == ""

    def test_invalid_question_stores_comma_joined_reasons(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        q_id = store_question(
            session,
            sent_id,
            _cloze(),
            make_validation(False, ["bare_pronoun_subject", "too_long"]),
        )
        session.commit()
        assert session.get(Question, q_id).validation_reasons == "bare_pronoun_subject,too_long"


class TestDiscardedDefault:
    def test_discarded_defaults_to_false(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        q_id = store_question(session, sent_id, _cloze(), make_validation(True))
        session.commit()
        assert session.get(Question, q_id).discarded is False


class TestTransactions:
    def test_ids_available_after_flush_before_commit(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        q_id = store_question(session, sent_id, _cloze(), make_validation(True))
        assert isinstance(doc_id, int) and doc_id > 0
        assert isinstance(sent_id, int) and sent_id > 0
        assert isinstance(q_id, int) and q_id > 0
        assert session.query(Document).count() == 1
        assert session.query(Question).count() == 1

    def test_rollback_discards_flushed_rows(self, session):
        doc_id = store_document(session, "lesson.pdf")
        sent_id = _stored_sentence(session, doc_id)
        store_question(session, sent_id, _cloze(), make_validation(True))
        assert session.query(Document).count() == 1
        session.rollback()
        assert session.query(Document).count() == 0
        assert session.query(Question).count() == 0

    def test_rollback_discards_partial_writes_on_failure(self, session):
        store_document(session, "lesson.pdf")
        with pytest.raises(IntegrityError):
            store_question(session, 999999, _cloze(), make_validation(True))
        session.rollback()
        assert session.query(Document).count() == 0
        assert session.query(Sentence).count() == 0

    def test_committed_data_readable_by_new_session(self, tmp_path):
        engine = create_db_engine(str(tmp_path / "store.db"))
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine)
        first = factory()
        doc_id = store_document(first, "lesson.pdf")
        first.commit()
        first.close()
        second = factory()
        doc = second.get(Document, doc_id)
        assert doc is not None
        assert doc.filename == "lesson.pdf"
        second.close()
        engine.dispose()


class TestPipelineToStore:
    def test_end_to_end_pipeline_to_store(self, session):
        analyzed = make_analyzed(
            "Cells are the basic unit of life.",
            nouns=["Cells", "unit", "life"],
            root_verb="are",
            subject_text="Cells",
        )
        scored = score_sentence(analyzed)
        cloze = generate_cloze(analyzed)
        validation = validate_question(analyzed, cloze)
        assert scored.worth_question is True
        assert cloze is not None

        doc_id = store_document(session, "lesson.pdf")
        sent_id = store_sentences(session, doc_id, [scored])[0]
        store_questions(session, [(sent_id, cloze, validation)])
        session.commit()

        question = (
            session.query(Question)
            .join(Sentence, Question.sentence_id == Sentence.id)
            .join(Document, Sentence.document_id == Document.id)
            .one()
        )
        assert question.answer == "Cells"
        assert question.text == "_____ are the basic unit of life."
        assert question.reason == "noun"
        assert question.is_valid is True
        assert question.validation_reasons == ""
        assert question.sentence.text == "Cells are the basic unit of life."
        assert question.sentence.document.filename == "lesson.pdf"


class TestMigration:
    def test_alembic_migration_creates_schema(self, tmp_path):
        db_path = tmp_path / "migrated.db"
        cfg = Config(str(REPO_ROOT / "core" / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")

        engine = create_db_engine(str(db_path))
        with engine.connect() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert {"documents", "sentences", "questions"} <= tables

            question_cols = {
                row[1] for row in conn.execute(sa.text("PRAGMA table_info(questions)"))
            }
            assert "discarded" in question_cols

            conn.execute(
                sa.text("INSERT INTO documents (filename) VALUES ('lesson.pdf')")
            )
            doc_id = conn.execute(sa.text("SELECT id FROM documents")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO sentences (document_id, position, text, worth_question, score_reason) "
                    "VALUES (:document_id, 0, 'Cells are the basic unit of life.', 1, 'factual_claim')"
                ),
                {"document_id": doc_id},
            )
            sent_id = conn.execute(sa.text("SELECT id FROM sentences")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO questions (sentence_id, text, answer, reason, is_valid, validation_reasons) "
                    "VALUES (:sentence_id, '_____ are the basic unit of life.', 'Cells', 'noun', 1, '')"
                ),
                {"sentence_id": sent_id},
            )
            discarded = conn.execute(
                sa.text("SELECT discarded FROM questions")
            ).scalar()
            assert discarded == 0
        engine.dispose()
