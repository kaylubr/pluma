from core.services.generate import GeneratedCloze
from core.services.validate import ValidationResult

# Document-level, post-Generate stage: no per-sentence stage has visibility
# across a whole document, so none can notice that the same answer was already
# used earlier in the deck. Duplicates are marked discarded (reusing the
# existing manual-discard mechanism) rather than dropped, which preserves an
# audit trail and requires no schema change.
DedupeItem = tuple[int, GeneratedCloze, ValidationResult]
DedupeResult = tuple[int, GeneratedCloze, ValidationResult, bool]


def _normalized_answer(answer: str) -> str:
    return answer.strip().lower()


def dedupe_questions(items: list[DedupeItem]) -> list[DedupeResult]:
    """Mark every valid question whose normalized answer already appeared in an
    earlier valid question as discarded."""
    seen_answers: set[str] = set()
    result: list[DedupeResult] = []
    for sentence_id, cloze, validation in items:
        discarded = False
        if validation.is_valid:
            normalized = _normalized_answer(cloze.answer)
            if normalized in seen_answers:
                discarded = True
            else:
                seen_answers.add(normalized)
        result.append((sentence_id, cloze, validation, discarded))
    return result
