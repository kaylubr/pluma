import pytest
from unittest.mock import patch
from core.services.extractors import extract_text


class TestExtractors:
    def test_dispatches_to_pdf_extractor(self):
        with patch("core.services.extractors.extract_pdf", return_value="pdf content") as mock_fn:
            result = extract_text("lesson.pdf", b"fake bytes")
        mock_fn.assert_called_once()
        assert result == "pdf content"


    def test_dispatches_to_pptx_extractor(self):
        with patch("core.services.extractors.extract_pptx", return_value="pptx content") as mock_fn:
            result = extract_text("lesson.pptx", b"fake bytes")
        mock_fn.assert_called_once()
        assert result == "pptx content"

    def test_unsupported_file_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text("lesson.exe", b"fake bytes")