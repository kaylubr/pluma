from core.services.analyze import AnalyzedSentence
from core.services.generate import GeneratedCloze


def make_analyzed(
    text: str,
    entities: list[tuple[str, str]] | None = None,
    nouns: list[str] | None = None,
    *,
    subject_is_pronoun: bool = False,
) -> AnalyzedSentence:
    return AnalyzedSentence(
        text=text,
        entities=entities or [],
        nouns=nouns or [],
        root_verb=None,
        subject_text=None,
        subject_is_pronoun=subject_is_pronoun,
    )


def make_cloze(sentence: str, text: str, answer: str, reason: str = "noun") -> GeneratedCloze:
    return GeneratedCloze(sentence=sentence, text=text, answer=answer, reason=reason)
