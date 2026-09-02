import re
from dataclasses import dataclass

from core.services.analyze import AnalyzedSentence


@dataclass
class GeneratedCloze:
    sentence: str
    text: str
    answer: str
    reason: str


_BLANK = "_____"

_NUMERIC_LABELS = frozenset(
    {"DATE", "TIME", "CARDINAL", "ORDINAL", "QUANTITY", "PERCENT", "MONEY"}
)

_HYPHEN_BRIDGE_PATTERN = re.compile(r"\s-\s")
_MAX_ENTITY_WORDS = 6


def _pattern(term: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)")


def _occurs_exactly_once(text: str, term: str) -> bool:
    return len(_pattern(term).findall(text)) == 1


def _is_incoherent_entity_span(term: str) -> bool:
    """Reject entity spans that look like NER bridged two clauses."""
    if _HYPHEN_BRIDGE_PATTERN.search(term):
        return True
    if len(term.split()) > _MAX_ENTITY_WORDS:
        return True
    return False


def _pick_candidate(analyzed: AnalyzedSentence) -> tuple[str, str] | None:
    candidates = [
        (term, "entity")
        for term, label in analyzed.entities
        if label not in _NUMERIC_LABELS
        and not _is_incoherent_entity_span(term)
    ] + [
        (term, "phrase") for term in analyzed.noun_phrases
    ] + [(term, "noun") for term in analyzed.nouns]
    for term, reason in candidates:
        if _occurs_exactly_once(analyzed.text, term):
            return term, reason
    return None


def generate_cloze(analyzed: AnalyzedSentence) -> GeneratedCloze | None:
    picked = _pick_candidate(analyzed)
    if picked is None:
        return None
    term, reason = picked
    blanked = _pattern(term).sub(_BLANK, analyzed.text, count=1)
    return GeneratedCloze(
        sentence=analyzed.text,
        text=blanked,
        answer=term,
        reason=reason,
    )


def generate_clozes(analyzed: list[AnalyzedSentence]) -> list[GeneratedCloze | None]:
    return [generate_cloze(sentence) for sentence in analyzed]
