from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from core.api.dependencies import get_db
from core.db.session import create_db_engine
from core.main import app
from core.models import Base
from core.services import store
from core.tests.helper import TINY_PDF, make_cloze, make_scored, make_validation

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

client = TestClient(app)


@pytest.fixture
def factory(tmp_path):
    engine = create_db_engine(str(tmp_path / "test.db"))
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def override_get_db():
        s = factory()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield factory
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _seed(factory):
    s = factory()
    doc_id = store.store_document(s, "lesson.pdf")
    first_id = store.store_sentences(
        s,
        doc_id,
        [make_scored("Cells are the basic unit of life.", True, "factual_claim")],
    )[0]
    second_id = store.store_sentences(
        s,
        doc_id,
        [make_scored("Both organelles have their own DNA", True, "factual_claim")],
    )[0]
    valid_id = store.store_question(
        s,
        first_id,
        make_cloze("Cells are the basic unit of life.", "_____ are the basic unit of life.", "Cells"),
        make_validation(True),
    )
    store.store_question(
        s,
        first_id,
        make_cloze("Cells divide.", "_____ divide.", "Cells"),
        make_validation(False, ["too_short"]),
    )
    discarded_id = store.store_question(
        s,
        second_id,
        make_cloze("Both organelles have their own DNA", "Both _____ have their own DNA", "organelles"),
        make_validation(True),
    )
    store.set_question_discarded(s, discarded_id, True)
    s.commit()
    s.close()
    return doc_id, valid_id, discarded_id


class TestCreateReviewer:
    def test_upload_pdf_creates_reviewer(self, factory):
        with open(FIXTURES / "lesson.pdf", "rb") as f:
            response = client.post(
                "/reviewers",
                files={"file": ("lesson.pdf", f.read(), "application/pdf")},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "lesson.pdf"
        assert data["id"] > 0
        assert isinstance(data["questions"], list)
        assert data["questions"]
        required = {"id", "sentence_id", "sentence_text", "text", "answer", "reason", "is_valid", "discarded"}
        assert required <= data["questions"][0].keys()

    def test_upload_pptx_creates_reviewer(self, factory):
        with open(FIXTURES / "slides.pptx", "rb") as f:
            response = client.post(
                "/reviewers",
                files={"file": ("slides.pptx", f.read(), "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
            )
        assert response.status_code == 201
        assert response.json()["filename"] == "slides.pptx"
        assert response.json()["questions"] == []

    def test_zero_question_upload_returns_empty_list(self, factory):
        response = client.post(
            "/reviewers",
            files={"file": ("empty.pdf", TINY_PDF, "application/pdf")},
        )
        assert response.status_code == 201
        assert response.json()["questions"] == []

    def test_unsupported_type_returns_400(self, factory):
        response = client.post(
            "/reviewers",
            files={"file": ("lesson.docx", b"bytes", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_empty_filename_returns_422(self, factory):
        response = client.post(
            "/reviewers",
            files={"file": ("", b"bytes", "application/pdf")},
        )
        assert response.status_code == 422


class TestListReviewers:
    def test_lists_reviewer_summaries(self, factory):
        _seed(factory)
        response = client.get("/reviewers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"] == "lesson.pdf"
        assert data[0]["question_count"] == 1

    def test_empty_database(self, factory):
        assert client.get("/reviewers").json() == []


class TestGetReviewerQuestions:
    def test_returns_only_valid_non_discarded(self, factory):
        doc_id, valid_id, _ = _seed(factory)
        response = client.get(f"/reviewers/{doc_id}/questions")
        assert response.status_code == 200
        data = response.json()
        assert [q["id"] for q in data] == [valid_id]
        assert data[0]["answer"] == "Cells"
        assert data[0]["discarded"] is False

    def test_unknown_reviewer_returns_404(self, factory):
        response = client.get("/reviewers/9999/questions")
        assert response.status_code == 404
        assert response.json()["detail"] == "Reviewer not found"


class TestDiscardQuestion:
    def test_discard_hides_question(self, factory):
        doc_id, valid_id, _ = _seed(factory)
        response = client.patch(f"/questions/{valid_id}", json={"discarded": True})
        assert response.status_code == 200
        assert response.json()["discarded"] is True
        assert client.get(f"/reviewers/{doc_id}/questions").json() == []

    def test_restore_brings_question_back(self, factory):
        doc_id, valid_id, _ = _seed(factory)
        client.patch(f"/questions/{valid_id}", json={"discarded": True})
        response = client.patch(f"/questions/{valid_id}", json={"discarded": False})
        assert response.status_code == 200
        assert response.json()["discarded"] is False
        questions = client.get(f"/reviewers/{doc_id}/questions").json()
        assert [q["id"] for q in questions] == [valid_id]

    def test_unknown_question_returns_404(self, factory):
        response = client.patch("/questions/9999", json={"discarded": True})
        assert response.status_code == 404
        assert response.json()["detail"] == "Question not found"

    def test_invalid_body_returns_422(self, factory):
        _, valid_id, _ = _seed(factory)
        response = client.patch(f"/questions/{valid_id}", json={"discarded": {"nested": True}})
        assert response.status_code == 422
