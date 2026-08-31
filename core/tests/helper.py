from core.services.analyze import AnalyzedSentence
from core.services.generate import GeneratedCloze
from core.services.score import ScoredSentence
from core.services.validate import ValidationResult

# A minimal hand-written PDF whose text ("Key organelles:") scores out to zero
# questions. pdfminer parses it despite the abbreviated xref.
TINY_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
    b"/Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    b"4 0 obj\n<< /Length 56 >>\nstream\n"
    b"BT /F1 12 Tf 72 720 Td (Key organelles:) Tj ET\n"
    b"endstream\nendobj\n"
    b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF"
)


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
