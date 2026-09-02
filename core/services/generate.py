import re
from dataclasses import dataclass

from wordfreq import zipf_frequency

from core.services.analyze import AnalyzedSentence, Candidate


@dataclass
class GeneratedCloze:
    sentence: str
    text: str
    answer: str
    reason: str


_BLANK = "_____"

_KIND_RANK = {"entity": 0, "phrase": 1, "noun": 2}


def _pattern(term: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)")


def _occurs_exactly_once(text: str, term: str) -> bool:
    return len(_pattern(term).findall(text)) == 1


def _term_rarity(term: str) -> float:
    """Rarity score for a candidate: lower is rarer. A phrase's score is the
    rarity of its rarest word, so "mutual exclusion" is not penalized for the
    common "mutual". Words absent from the frequency reference score 0.0 and
    are treated as maximally rare."""
    return min(zipf_frequency(word.lower(), "en") for word in term.split())


def _candidate_key(candidate: Candidate) -> tuple[int, float]:
    """Ordinal ranking: whole concepts before sub-parts, rarer before common.
    Structural hygiene and identifier demotion are handled upstream in
    Analyze's candidate construction, so this only orders eligible spans."""
    return (_KIND_RANK[candidate.kind], _term_rarity(candidate.text))


def _eligible(candidate: Candidate) -> bool:
    return candidate.rejected is None and not candidate.identifier_like


def generate_candidate_clozes(analyzed: AnalyzedSentence) -> list[GeneratedCloze]:
    """Rank every eligible candidate into a cloze. Each candidate is kept only
    if it blanks a span that occurs exactly once, so the returned list is the
    set of reconstructable clozes in preference order. The same span often
    surfaces as an entity, a phrase, and a noun; only the highest-ranked cloze
    for a given (frame, answer) is kept."""
    candidates = sorted(
        (candidate for candidate in analyzed.candidates if _eligible(candidate)),
        key=_candidate_key,
    )
    result: list[GeneratedCloze] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        if not _occurs_exactly_once(analyzed.text, candidate.text):
            continue
        blanked = _pattern(candidate.text).sub(_BLANK, analyzed.text, count=1)
        key = (blanked, candidate.text)
        if key in seen:
            continue
        seen.add(key)
        result.append(
            GeneratedCloze(
                sentence=analyzed.text,
                text=blanked,
                answer=candidate.text,
                reason=candidate.kind,
            )
        )
    return result


def generate_cloze(analyzed: AnalyzedSentence) -> GeneratedCloze | None:
    candidates = generate_candidate_clozes(analyzed)
    return candidates[0] if candidates else None


def generate_clozes(analyzed: list[AnalyzedSentence]) -> list[GeneratedCloze | None]:
    return [generate_cloze(sentence) for sentence in analyzed]
