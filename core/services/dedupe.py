import re

from core.services.generate import GeneratedCloze
from core.services.validate import ValidationResult

# Document-level selection stage: no per-sentence stage can see across a whole
# document, so none can notice that the deck already covers this card. A card
# is redundant when its surface (blanked frame + answer) overlaps an earlier
# valid card's almost completely — duplicated slide content, or the same
# passage where the answer surfaced with case/plural drift. A repeated answer
# inside genuinely different questions is NOT redundant, so no never-repeat-an-
# answer rule is applied. Redundancy between different concepts (e.g. "mutual
# exclusion" vs. "deadlock") is meaning, not surface form, and is out of scope.
# Duplicates are marked discarded (reusing the existing manual-discard
# mechanism) rather than dropped, which preserves an audit trail.
DedupeItem = tuple[int, GeneratedCloze, ValidationResult]
DedupeResult = tuple[int, GeneratedCloze, ValidationResult, bool]

_OVERLAP_THRESHOLD = 0.75


def _card_signature(cloze: GeneratedCloze) -> frozenset[str]:
    return frozenset(
        re.findall(r"[a-z0-9]+", (f"{cloze.text} {cloze.answer}").lower())
    )


def _overlap(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def dedupe_questions(items: list[DedupeItem]) -> list[DedupeResult]:
    """Mark every valid card that is a near-duplicate of an earlier valid card
    as discarded. Invalid questions are never compared and pass through
    untouched."""
    kept_signatures: list[frozenset[str]] = []
    result: list[DedupeResult] = []
    for sentence_id, cloze, validation in items:
        discarded = False
        if validation.is_valid:
            signature = _card_signature(cloze)
            if any(
                _overlap(signature, kept) >= _OVERLAP_THRESHOLD
                for kept in kept_signatures
            ):
                discarded = True
            else:
                kept_signatures.append(signature)
        result.append((sentence_id, cloze, validation, discarded))
    return result
