from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_upload_multiple_files():
    with patch("app.main.extract_text", side_effect=["pdf text", "pptx text"]):
        response = client.post(
            "/upload",
            files=[
                ("files", ("lesson.pdf", b"fake pdf bytes", "application/pdf")),
                ("files", ("slides.pptx", b"fake pptx bytes", "application/vnd.openxmlformats-officedocument.presentationml.presentation")),
            ]
        )

    print(response.json())

    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["text"] == "pdf text"
    assert results[1]["text"] == "pptx text"


def test_upload_single_pdf():
    with patch("app.main.extract_text", return_value="extracted pdf content"):
        response = client.post(
            "/upload/single",
            files={"file": ("lesson.pdf", b"fake pdf bytes", "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "lesson.pdf"
    assert data["text"] == "extracted pdf content"
    assert data["error"] is None


def test_upload_single_pptx():
    with patch("app.main.extract_text", return_value="extracted pptx content"):
        response = client.post(
            "/upload/single",
            files={"file": ("slides.pptx", b"fake pptx bytes", "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "slides.pptx"
    assert data["text"] == "extracted pptx content"
    assert data["error"] is None


def test_upload_single_unsupported_type():
    response = client.post(
        "/upload/single",
        files={"file": ("document.docx", b"fake docx bytes", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Unsupported file type" in data["detail"]


def test_upload_single_txt_rejected():
    response = client.post(
        "/upload/single",
        files={"file": ("notes.txt", b"fake txt bytes", "text/plain")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Unsupported file type" in data["detail"]


def test_upload_single_empty_filename():
    response = client.post(
        "/upload/single",
        files={"file": ("", b"fake bytes", "application/pdf")},
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data