import re
from dataclasses import dataclass

from core.services.analyze import AnalyzedSentence


@dataclass
class ScoredSentence:
    text: str
    worth_question: bool
    reason: str


MIN_WORDS = 2

_STEP_LABEL_PATTERN = re.compile(r"^(?:step|phase|part)\s+\d+\b", re.IGNORECASE)

_FLOW_NOTATION_PATTERN = re.compile(r"(?:\u2192|\u2190|\u21d2|->|=>)")

_ALPHA_RATIO_THRESHOLD = 0.5

_WH_WORDS = frozenset(
    {"what", "which", "who", "whom", "whose", "why", "how", "where", "when"}
)

_AUX_START = frozenset(
    {
        "is", "are", "was", "were",
        "do", "does", "did",
        "has", "have", "had",
        "can", "could", "will", "would", "should",
        "may", "might", "must",
    }
)


_IMPERATIVE_VERBS = frozenset(
    {
        "define", "explain", "describe", "list", "compare", "discuss",
        "summarize", "state", "outline", "give", "name", "identify",
        "review", "distinguish", "evaluate", "examine", "show", "illustrate",
        "consider", "note", "remember", "recall", "answer", "solve",
        "compute", "calculate",
    }
)


_BOILERPLATE_OPENS = frozenset(
    {
        "introduction", "overview", "summary", "references", "takeaways",
        "objectives", "agenda", "conclusion", "thank", "thanks", "questions",
        "discussion", "quiz", "contents", "welcome", "end",
    }
)


def _is_interrogative(analyzed: AnalyzedSentence) -> bool:
    text = analyzed.text.strip()
    if text.endswith("?"):
        return True
    tokens = text.split()
    if not tokens:
        return False
    first = tokens[0].lower()
    if first in _WH_WORDS:
        return True
    if first in _AUX_START:
        return True
    return False


def _is_symbol_heavy(text: str) -> bool:
    non_space = [ch for ch in text if not ch.isspace()]
    if not non_space:
        return False
    alpha = sum(ch.isalpha() for ch in non_space)
    return alpha / len(non_space) < _ALPHA_RATIO_THRESHOLD


def score_sentence(analyzed: AnalyzedSentence) -> ScoredSentence:
    text = analyzed.text
    if not text or not text.strip():
        return ScoredSentence(text=text, worth_question=False, reason="empty")

    words = text.strip().split()
    if len(words) < MIN_WORDS:
        return ScoredSentence(text=text, worth_question=False, reason="too_short")

    if _STEP_LABEL_PATTERN.match(text.strip()):
        return ScoredSentence(text=text, worth_question=False, reason="step_label")

    if _FLOW_NOTATION_PATTERN.search(text):
        return ScoredSentence(text=text, worth_question=False, reason="notation")

    if _is_symbol_heavy(text):
        return ScoredSentence(text=text, worth_question=False, reason="symbol_heavy")

    if _is_interrogative(analyzed):
        return ScoredSentence(text=text, worth_question=False, reason="interrogative")

    if analyzed.root_verb and analyzed.root_verb.lower() in _IMPERATIVE_VERBS:
        return ScoredSentence(text=text, worth_question=False, reason="imperative")

    if words[0].lower().strip(":,.;") in _BOILERPLATE_OPENS:
        return ScoredSentence(text=text, worth_question=False, reason="boilerplate")

    if analyzed.root_verb is None:
        return ScoredSentence(text=text, worth_question=False, reason="no_verb")

    if analyzed.entities and analyzed.root_verb:
        return ScoredSentence(text=text, worth_question=True, reason="named_entity")

    if analyzed.root_verb and analyzed.subject_text and analyzed.nouns:
        return ScoredSentence(text=text, worth_question=True, reason="factual_claim")

    return ScoredSentence(text=text, worth_question=False, reason="no_claim")


def score_sentences(analyzed: list[AnalyzedSentence]) -> list[ScoredSentence]:
    return [score_sentence(sentence) for sentence in analyzed]