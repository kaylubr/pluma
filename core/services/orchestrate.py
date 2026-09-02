from sqlalchemy.orm import Session

from core.services import store
from core.services.analyze import analyze_sentence
from core.services.clean import clean_markdown
from core.services.extractors import extract_text
from core.services.generate import generate_candidate_clozes
from core.services.score import score_sentence
from core.services.selection import select_document_questions
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

    pools = []
    for sentence_id, (analyzed, _) in zip(sentence_ids, kept):
        clozes = generate_candidate_clozes(analyzed)
        if not clozes:
            continue
        validated = [(cloze, validate_question(analyzed, cloze)) for cloze in clozes]
        pools.append((sentence_id, validated))
    store.store_questions(session, select_document_questions(pools))

    return document_id
