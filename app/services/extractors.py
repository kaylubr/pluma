from markitdown import MarkItDown
import io


def extract_pdf(contents: bytes) -> str:
    md = MarkItDown()
    result = md.convert_stream(io.BytesIO(contents), file_extension=".pdf")
    return result.text_content


def extract_pptx(contents: bytes) -> str:
    md = MarkItDown()
    result = md.convert_stream(io.BytesIO(contents), file_extension=".pptx")
    return result.text_content


def extract_text(filename: str, contents: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return extract_pdf(contents)
    elif ext == "pptx":
        return extract_pptx(contents)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")