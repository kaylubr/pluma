import re


def clean_markdown(text: str) -> str:
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

        if re.match(r"^[-*+]\s+", stripped):
            content = re.sub(r"^[-*+]\s+", "", stripped)
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

        if line.strip():
            cleaned_lines.append(line.strip())

    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()