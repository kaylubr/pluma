from dataclasses import dataclass
from spacy.tokens import Token
from core.services.nlp import get_analyzer


@dataclass
class AnalyzedSentence:
    text: str
    entities: list[tuple[str, str]]
    nouns: list[str]
    root_verb: str | None
    subject_text: str | None
    subject_is_pronoun: bool
    noun_phrases: list[str]


def _noun_phrases(doc) -> list[str]:
    root_index = next(token.i for token in doc if token.head == token)
    phrases = []
    for chunk in doc.noun_chunks:
        if root_index in range(chunk.start, chunk.end):
            continue
        start = chunk.start + (1 if chunk[0].dep_ == "det" else 0)
        if start >= chunk.end:
            continue
        phrases.append(doc[start : chunk.end].text)
    return phrases


def analyze_sentence(text: str) -> AnalyzedSentence:
    if not text or not text.strip():
        return AnalyzedSentence(
            text=text,
            entities=[],
            nouns=[],
            root_verb=None,
            subject_text=None,
            subject_is_pronoun=False,
            noun_phrases=[],
        )

    nlp = get_analyzer()
    doc = nlp(text)

    entities: list[tuple[str, str]] = [(ent.text, ent.label_) for ent in doc.ents]

    nouns: list[str] = [token.text for token in doc if token.pos_ in ("NOUN", "PROPN")]

    noun_phrases = _noun_phrases(doc)

    root_verb: str | None = None
    root_token: Token | None = None
    for token in doc:
        if token.dep_ == "ROOT":
            if token.pos_ in ("VERB", "AUX"):
                root_verb = token.text
                root_token = token
            break
    if root_verb is None:
        # en_core_web_sm occasionally picks a noun as ROOT (e.g. unpunctuated
        # PPTX bullets like "Ribosomes synthesize proteins"); fall back to the
        # first verb so the main-verb signal isn't lost for downstream stages.
        for token in doc:
            if token.pos_ in ("VERB", "AUX"):
                root_verb = token.text
                root_token = token
                break

    subject_text: str | None = None
    subject_is_pronoun: bool = False
    for token in doc:
        if token.dep_ in ("nsubj", "nsubjpass"):
            subject_text = doc[token.left_edge.i : token.right_edge.i + 1].text
            subject_is_pronoun = token.pos_ == "PRON"
            break
    if subject_text is None and root_token is not None:
        # The same model error can miss the subject relation entirely (the
        # subject tagged ADV, e.g. "Ribosomes" in the sentence above); fall
        # back to the closest pre-verbal dependent of the main verb.
        for token in doc:
            if token.i < root_token.i and token.head == root_token:
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
        noun_phrases=noun_phrases,
    )
