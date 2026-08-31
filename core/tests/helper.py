from core.services.analyze import AnalyzedSentence
from core.services.generate import GeneratedCloze
from core.services.score import ScoredSentence
from core.services.validate import ValidationResult


def make_analyzed(
    text: str,
    entities: list[tuple[str, str]] | None = None,
    nouns: list[str] | None = None,
    *,
    root_verb: str | None = None,
    subject_text: str | None = None,
    subject_is_pronoun: bool = False,
) -> AnalyzedSentence:
    return AnalyzedSentence(
        text=text,
        entities=entities or [],
        nouns=nouns or [],
        root_verb=root_verb,
        subject_text=subject_text,
        subject_is_pronoun=subject_is_pronoun,
    )


def make_cloze(sentence: str, text: str, answer: str, reason: str = "noun") -> GeneratedCloze:
    return GeneratedCloze(sentence=sentence, text=text, answer=answer, reason=reason)


def make_scored(text: str, worth_question: bool, reason: str) -> ScoredSentence:
    return ScoredSentence(text=text, worth_question=worth_question, reason=reason)


def make_validation(is_valid: bool, reasons: list[str] | None = None) -> ValidationResult:
    return ValidationResult(is_valid=is_valid, reasons=reasons or [])
