import re

# Literal Unicode bullet glyphs that some extractions emit instead of markdown
# list markers. They are formatting noise, not content, so strip them before
# anything downstream sees the text — otherwise they reach spaCy and can get
# folded into an entity (e.g. "• Custom" tagged as a single GPE).
_BULLET_GLYPHS = "•◦‣▪▫⁃"

_BULLET_LINE_PATTERN = re.compile(rf"^[-*+{_BULLET_GLYPHS}]\s+")
_BULLET_GLYPH_PATTERN = re.compile(f"[{_BULLET_GLYPHS}]")


def clean_markdown(text: str, source_format: str = "pdf") -> str:
    if not text or not text.strip():
        return ""

    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            cleaned_lines.append("")
            continue

        if stripped.startswith("#"):
            continue

        # Bullet and numbered-list markers are owned by Split for PPTX, which
        # needs them to know where one bullet ends and the next begins; only
        # strip them for PDF text.
        if source_format == "pdf":
            if _BULLET_LINE_PATTERN.match(stripped):
                content = _BULLET_LINE_PATTERN.sub("", stripped)
                cleaned_lines.append(content)
                continue

            if re.match(r"^\d+\.\s+", stripped):
                content = re.sub(r"^\d+\.\s+", "", stripped)
                cleaned_lines.append(content)
                continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            continue

        if "|" in stripped:
            continue

        line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", line)

        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"__(.+?)__", r"\1", line)
        line = re.sub(r"\*(.+?)\*", r"\1", line)
        line = re.sub(r"_(.+?)_", r"\1", line)

        line = _BULLET_GLYPH_PATTERN.sub("", line)

        if line.strip():
            cleaned_lines.append(line.strip())

    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()