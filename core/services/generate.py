import re
from dataclasses import dataclass

from wordfreq import zipf_frequency

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


def _term_rarity(term: str) -> float:
    """Rarity score for a candidate: lower is rarer. A phrase's score is the
    rarity of its rarest word, so "mutual exclusion" is not penalized for the
    common "mutual". Words absent from the frequency reference score 0.0 and
    are treated as maximally rare."""
    return min(zipf_frequency(word.lower(), "en") for word in term.split())


def _pick_candidate(analyzed: AnalyzedSentence) -> tuple[str, str] | None:
    entity_candidates = [
        (term, "entity")
        for term, label in analyzed.entities
        if label not in _NUMERIC_LABELS
        and not _is_incoherent_entity_span(term)
    ]
    phrase_candidates = sorted(
        ((term, "phrase") for term in analyzed.noun_phrases),
        key=lambda candidate: _term_rarity(candidate[0]),
    )
    noun_candidates = sorted(
        ((term, "noun") for term in analyzed.nouns),
        key=lambda candidate: _term_rarity(candidate[0]),
    )
    candidates = entity_candidates + phrase_candidates + noun_candidates
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
