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