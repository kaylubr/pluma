import spacy


_sentencizer_nlp = spacy.blank("en")
_sentencizer_nlp.add_pipe("sentencizer")


def _rejoin_wrapped_lines(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    joined = []
    buffer = ""
    for line in lines:
        buffer = f"{buffer} {line}".strip() if buffer else line
        if buffer.endswith((".", "!", "?")):
            joined.append(buffer)
            buffer = ""
    if buffer:
        joined.append(buffer)
    return " ".join(joined)


def split_sentences(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    rejoined = _rejoin_wrapped_lines(text)
    doc = _sentencizer_nlp(rejoined)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    return sentences