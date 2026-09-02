import re

from .nlp import get_sentencizer


_sentencizer_nlp = get_sentencizer()

_BULLET_PATTERN = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_NUMBERED_PATTERN = re.compile(r"^(\s*)\d+\.\s+(.*)$")


def _has_unbalanced_open_parenthesis(text: str) -> bool:
    return text.count("(") > text.count(")")


def _should_join(current: str, next_line: str) -> bool:
    # An open parenthesis that never closes on the line means the parenthetical
    # continues onto the next line (e.g. a numeric list split mid-value), so
    # join regardless of how the next line starts.
    if _has_unbalanced_open_parenthesis(current):
        return True
    # A line ending in a comma or semicolon is never a sentence boundary in
    # edited prose, so it always continues into the next line.
    if current.endswith((",", ";")):
        return True
    # A line ending in terminal punctuation is complete on its own.
    if current.endswith((".", "!", "?")):
        return False
    # Otherwise (no terminal punctuation, no trailing comma or semicolon), join
    # only if the next line continues in lowercase — the sign of a sentence
    # broken mid-clause by column wrapping. A new thought, bullet, or fragment
    # almost always starts capitalized. Defaulting to a boundary is deliberate:
    # under-merging leaves fragments that Score's no_verb and too_short rules
    # already reject, while over-merging creates fake sentences that slip past
    # every downstream guard.
    return next_line[:1].islower()


def _split_pdf(text: str) -> list[str]:
    """Split PDF text into sentences using line-rejoining heuristic + sentencizer."""
    if not text or not text.strip():
        return []

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    logical_lines: list[str] = []
    current = lines[0] if lines else ""
    for next_line in lines[1:]:
        if _should_join(current, next_line):
            current = f"{current} {next_line}"
        else:
            logical_lines.append(current)
            current = next_line
    if current:
        logical_lines.append(current)

    sentences: list[str] = []
    for logical_line in logical_lines:
        doc = _sentencizer_nlp(logical_line)
        sentences.extend(
            sent.text.strip() for sent in doc.sents if sent.text.strip()
        )
    return sentences


def _split_pptx(text: str) -> list[str]:
    """Split PPTX text into sentences treating bullets/numbered items as separate entries."""
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
    """Split text into sentences based on source format (pdf or pptx)."""
    if not text or not text.strip():
        return []

    if source_format == "pptx":
        return _split_pptx(text)
    elif source_format == "pdf":
        return _split_pdf(text)
    else:
        raise ValueError(f"Unknown source_format: {source_format}. Expected 'pdf' or 'pptx'.")