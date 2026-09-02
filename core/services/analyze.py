import re
from dataclasses import dataclass
from spacy.tokens import Token
from core.services.nlp import get_analyzer


@dataclass(frozen=True)
class Candidate:
    """A span worth blanking, surfaced from Analyze so downstream stages rank
    real concept units instead of re-deriving them from flat token lists."""

    text: str
    kind: str  # "entity" | "phrase" | "noun"
    entity_label: str | None
    identifier_like: bool
    rejected: str | None  # structural reason this span must never be blanked


@dataclass
class AnalyzedSentence:
    text: str
    entities: list[tuple[str, str]]
    nouns: list[str]
    root_verb: str | None
    subject_text: str | None
    subject_is_pronoun: bool
    noun_phrases: list[str]
    candidates: list[Candidate] | None = None

    def __post_init__(self) -> None:
        if self.candidates is None:
            self.candidates = _derive_candidates(
                self.entities, self.noun_phrases, self.nouns
            )


_NUMERIC_LABELS = frozenset(
    {"DATE", "TIME", "CARDINAL", "ORDINAL", "QUANTITY", "PERCENT", "MONEY"}
)

_HYPHEN_BRIDGE_PATTERN = re.compile(r"\s-\s")
_MAX_SPAN_WORDS = 6


def _hygiene_reason(text: str, kind: str, entity_label: str | None) -> str | None:
    if kind == "entity" and entity_label in _NUMERIC_LABELS:
        return "numeric"
    if len(text) == 1 and (text.isalpha() or text.isdigit()):
        return "single_letter"
    if _HYPHEN_BRIDGE_PATTERN.search(text):
        return "hyphen_bridge"
    if len(text.split()) > _MAX_SPAN_WORDS:
        return "too_many_words"
    return None


def _identifier_like(text: str) -> bool:
    """True when a span reads as a diagram/identifier label rather than a
    concept: a bare single letter, or an alphanumeric token such as R1/P2."""
    for token in text.split():
        if len(token) == 1 and (token.isalpha() or token.isdigit()):
            return True
        if any(ch.isalpha() for ch in token) and any(ch.isdigit() for ch in token):
            return True
    return False


def _derive_candidates(
    entities: list[tuple[str, str]],
    noun_phrases: list[str],
    nouns: list[str],
) -> list[Candidate]:
    candidates = [
        Candidate(
            text=text,
            kind="entity",
            entity_label=label,
            identifier_like=_identifier_like(text),
            rejected=_hygiene_reason(text, "entity", label),
        )
        for text, label in entities
    ]
    phrases = [
        Candidate(
            text=text,
            kind="phrase",
            entity_label=None,
            identifier_like=_identifier_like(text),
            rejected=_hygiene_reason(text, "phrase", None),
        )
        for text in noun_phrases
    ]
    candidates.extend(phrases)
    identifier_words: set[str] = set()
    for span in candidates:
        if span.identifier_like:
            identifier_words.update(span.text.split())
    candidates.extend(
        Candidate(
            text=text,
            kind="noun",
            entity_label=None,
            identifier_like=_identifier_like(text) or any(
                word in identifier_words for word in text.split()
            ),
            rejected=_hygiene_reason(text, "noun", None),
        )
        for text in nouns
    )
    return candidates


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
