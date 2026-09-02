from sqlalchemy.orm import Session

from core.services import store
from core.services.analyze import analyze_sentence
from core.services.clean import clean_markdown
from core.services.dedupe import dedupe_questions
from core.services.extractors import extract_text
from core.services.generate import generate_cloze
from core.services.score import score_sentence
from core.services.split import split_sentences
from core.services.validate import validate_question


def process_document(session: Session, filename: str, contents: bytes) -> int:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ("pdf", "pptx"):
        raise ValueError(f"Unsupported file type: .{ext}. Only PDF and PPTX are supported.")

    text = extract_text(filename, contents)
    if not text or not text.strip():
        raise ValueError("No text could be extracted from the file.")

    cleaned = clean_markdown(text, source_format=ext)
    sentences = split_sentences(cleaned, ext)

    kept = []
    for sentence in sentences:
        analyzed = analyze_sentence(sentence)
        scored = score_sentence(analyzed)
        if scored.worth_question:
            kept.append((analyzed, scored))

    document_id = store.store_document(session, filename)
    sentence_ids = store.store_sentences(
        session, document_id, [scored for _, scored in kept]
    )

    items = []
    for sentence_id, (analyzed, _) in zip(sentence_ids, kept):
        cloze = generate_cloze(analyzed)
        if cloze is None:
            continue
        items.append((sentence_id, cloze, validate_question(analyzed, cloze)))
    store.store_questions(session, dedupe_questions(items))

    return document_id
