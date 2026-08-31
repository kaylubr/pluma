import re
from dataclasses import dataclass

from core.services.analyze import AnalyzedSentence
from core.services.generate import GeneratedCloze


@dataclass
class ValidationResult:
    is_valid: bool
    reasons: list[str]


MIN_WORDS = 5
MAX_WORDS = 30


def _pattern(term: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)")


def _count_occurrences(text: str, term: str) -> int:
    return len(_pattern(term).findall(text))


def validate_question(analyzed: AnalyzedSentence, cloze: GeneratedCloze) -> ValidationResult:
    reasons: list[str] = []

    word_count = len(analyzed.text.split())
    if word_count < MIN_WORDS:
        reasons.append("too_short")
    elif word_count > MAX_WORDS:
        reasons.append("too_long")

    if analyzed.subject_is_pronoun:
        reasons.append("bare_pronoun_subject")

    if _count_occurrences(analyzed.text, cloze.answer) > 1:
        reasons.append("ambiguous_blank")

    if _count_occurrences(cloze.text, cloze.answer) > 0:
        reasons.append("answer_leakage")

    return ValidationResult(is_valid=not reasons, reasons=reasons)


def validate_questions(
    analyzed: list[AnalyzedSentence],
    clozes: list[GeneratedCloze | None],
) -> list[ValidationResult]:
    if len(analyzed) != len(clozes):
        raise ValueError("analyzed and clozes must be parallel lists of equal length")

    results: list[ValidationResult] = []
    for sentence, cloze in zip(analyzed, clozes):
        if cloze is None:
            results.append(ValidationResult(is_valid=False, reasons=["no_question"]))
        else:
            results.append(validate_question(sentence, cloze))
    return results
