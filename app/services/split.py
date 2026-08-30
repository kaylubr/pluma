import re
import spacy


_sentencizer_nlp = spacy.blank("en")
_sentencizer_nlp.add_pipe("sentencizer")


_BULLET_PATTERN = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_NUMBERED_PATTERN = re.compile(r"^(\s*)\d+\.\s+(.*)$")


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


def _split_pptx(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    lines = text.split("\n")
    items = []
    current_item = ""
    in_bullet = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if current_item:
                items.append(current_item)
                current_item = ""
                in_bullet = False
            continue

        bullet_match = _BULLET_PATTERN.match(line)
        numbered_match = _NUMBERED_PATTERN.match(line)

        is_empty_bullet = stripped in ("-", "*", "+") or re.match(r"^\d+\.$", stripped)

        if bullet_match or numbered_match:
            if current_item:
                items.append(current_item)
            content = (bullet_match or numbered_match).group(2)
            content = content.strip()
            if content:
                current_item = content
                in_bullet = True
            else:
                current_item = ""
                in_bullet = False
        elif is_empty_bullet:
            if current_item:
                items.append(current_item)
            current_item = ""
            in_bullet = False
        else:
            if in_bullet and current_item and not current_item.endswith(":"):
                current_item = f"{current_item} {stripped}"
            else:
                if current_item:
                    items.append(current_item)
                current_item = stripped
                in_bullet = False

    if current_item:
        items.append(current_item)

    result = []
    for item in items:
        if not item.strip():
            continue
        doc = _sentencizer_nlp(item)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        result.extend(sentences)

    return result


def split_sentences(text: str, source_format: str = "pdf") -> list[str]:
    if not text or not text.strip():
        return []

    if source_format == "pptx":
        return _split_pptx(text)

    rejoined = _rejoin_wrapped_lines(text)
    doc = _sentencizer_nlp(rejoined)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    return sentences