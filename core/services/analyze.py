from dataclasses import dataclass

from core.services.nlp import get_analyzer


@dataclass
class AnalyzedSentence:
    text: str
    entities: list[tuple[str, str]]
    nouns: list[str]
    root_verb: str | None
    subject_text: str | None
    subject_is_pronoun: bool


def analyze_sentence(text: str) -> AnalyzedSentence:
    if not text or not text.strip():
        return AnalyzedSentence(
            text=text,
            entities=[],
            nouns=[],
            root_verb=None,
            subject_text=None,
            subject_is_pronoun=False,
        )

    nlp = get_analyzer()
    doc = nlp(text)

    entities: list[tuple[str, str]] = [(ent.text, ent.label_) for ent in doc.ents]

    nouns: list[str] = [token.text for token in doc if token.pos_ in ("NOUN", "PROPN")]

    root_verb: str | None = None
    for token in doc:
        if token.dep_ == "ROOT":
            if token.pos_ in ("VERB", "AUX"):
                root_verb = token.text
            break

    subject_text: str | None = None
    subject_is_pronoun: bool = False
    for token in doc:
        if token.dep_ in ("nsubj", "nsubjpass"):
            subject_text = doc[token.left_edge.i : token.right_edge.i + 1].text
            subject_is_pronoun = token.pos_ == "PRON"
            break

    return AnalyzedSentence(
        text=text,
        entities=entities,
        nouns=nouns,
        root_verb=root_verb,
        subject_text=subject_text,
        subject_is_pronoun=subject_is_pronoun,
    )
