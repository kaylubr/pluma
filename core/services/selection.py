import re

from core.services.generate import GeneratedCloze
from core.services.validate import ValidationResult

# Document-level selection stage: no per-sentence stage can see across a whole
# document, so none can notice that the deck already covers a card or that one
# concept has been blanked over and over. Selection walks the per-sentence
# candidate pools in document order and picks at most one winner per sentence,
# applying three independent, layered rules:
#   1. exact duplicate: an identical served question (same frame + answer)
#      already chosen — cheap string check, independent of any quality logic;
#   2. near-duplicate surface: token-overlap against already-chosen cards,
#      catching duplicated content with casing/plural drift;
#   3. concept-usage cap: an answer-concept (normalized answer) already used
#      _MAX_ANSWER_REUSE times falls back to the sentence's next-ranked
#      candidate, so a repeated concept cannot crowd the deck.
# A candidate that fails a rule is skipped, not marked discarded; if no
# candidate survives, the sentence yields no card at all. Structural validity
# is decided by Validate per candidate; a sentence with no structurally valid
# candidate still contributes its best-ranked card as an invalid marker so the
# audit trail and the "invalid questions are stored" behavior are preserved.
PoolItem = tuple[GeneratedCloze, ValidationResult]
SentencePools = list[tuple[int, list[PoolItem]]]
Selected = list[tuple[int, GeneratedCloze, ValidationResult]]

_MAX_ANSWER_REUSE = 2
_OVERLAP_THRESHOLD = 0.75


def _normalized_answer(answer: str) -> str:
    return answer.strip().lower()


def _card_signature(cloze: GeneratedCloze) -> frozenset[str]:
    return frozenset(
        re.findall(r"[a-z0-9]+", (f"{cloze.text} {cloze.answer}").lower())
    )


def _overlap(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def select_document_questions(pools: SentencePools) -> Selected:
    """Pick at most one winner per sentence in document order."""
    chosen: list[tuple[GeneratedCloze, ValidationResult]] = []
    concepts: dict[str, int] = {}
    selected: Selected = []

    for sentence_id, candidates in pools:
        valid = [(cloze, validation) for cloze, validation in candidates if validation.is_valid]

        if not valid:
            # Keep the best-ranked card as an invalid marker (historical
            # behavior: structurally invalid questions are still stored).
            if candidates:
                cloze, validation = candidates[0]
                selected.append((sentence_id, cloze, validation))
                chosen.append((cloze, validation))
            continue

        winner: PoolItem | None = None
        for cloze, validation in valid:
            key = _normalized_answer(cloze.answer)
            surface = (cloze.text, key)
            if any(surface == (c.text, _normalized_answer(c.answer)) for c, _ in chosen):
                continue
            signature = _card_signature(cloze)
            if any(
                _overlap(signature, _card_signature(c)) >= _OVERLAP_THRESHOLD
                for c, _ in chosen
            ):
                continue
            if concepts.get(key, 0) >= _MAX_ANSWER_REUSE:
                continue
            winner = (cloze, validation)
            break

        if winner is None:
            continue
        cloze, validation = winner
        key = _normalized_answer(cloze.answer)
        concepts[key] = concepts.get(key, 0) + 1
        selected.append((sentence_id, cloze, validation))
        chosen.append((cloze, validation))

    return selected
