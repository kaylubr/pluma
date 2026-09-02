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

# A comma-separated item immediately followed by a signed parenthetical number,
# e.g. "bad (-1)" in "skinny (-1), bad (-1), hate (-1)". Marks an example-value
# enumeration, not a claim.
_EXAMPLE_LIST_PATTERN = re.compile(
    r",\s*[A-Za-z][^,()]*\(\s*[+-]?\s*\d+(?:\.\d+)?\s*\)"
)

# A signed number immediately followed by a parenthetical gloss, e.g. the
# "+2 (thrilled) + 1.5 (amazing)" chain in a worked arithmetic example.
_WORKED_GLOSS_PATTERN = re.compile(r"[+-]\s*\d+(?:\.\d+)?\s*\(")

# Words that introduce an explicit noun-phrase subject ("then the system ...").
# A 'then' consequence starting with any other word is a bare imperative or a
# nominal fragment, i.e. procedural.
_EXPLICIT_SUBJECT_STARTERS = frozenset(
    {
        "the", "a", "an", "this", "that", "these", "those",
        "its", "their", "our", "your", "his", "her", "my",
        "each", "every", "some", "any", "all", "no", "one",
        "another", "both",
    }
)


def _is_pseudocode_conditional(text: str) -> bool:
    words = text.split()
    if not words:
        return False
    if words[0].lower().strip(":,.;") != "if":
        return False
    lower = text.lower()
    then_match = re.search(r"\bthen\b", lower)
    if then_match:
        # A 'then' consequence with no explicit subject ("then refuse the
        # request", "then deadlock") is a procedural branch, not a claim.
        after = lower[then_match.end():].strip()
        if not after:
            return True
        if after.split()[0].strip(":,.;") in _EXPLICIT_SUBJECT_STARTERS:
            return False
        return True
    # A lone condition with no 'then', no clause comma, and no terminal
    # punctuation is a flattened outline fragment ("If graph contains a
    # cycle"), whose apodosis lives in a sibling bullet.
    if "," not in text and not text.rstrip().endswith((".", "!", "?", ";")):
        return True
    return False


def _is_worked_example(text: str) -> bool:
    return "=" in text and len(_WORKED_GLOSS_PATTERN.findall(text)) >= 2

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

    if text.rstrip().endswith(":"):
        return ScoredSentence(text=text, worth_question=False, reason="lead_in")

    if _EXAMPLE_LIST_PATTERN.search(text):
        return ScoredSentence(text=text, worth_question=False, reason="example_list")

    if _is_pseudocode_conditional(text):
        return ScoredSentence(text=text, worth_question=False, reason="pseudocode_conditional")

    if _is_worked_example(text):
        return ScoredSentence(text=text, worth_question=False, reason="worked_example")

    if _is_interrogative(analyzed):
        return ScoredSentence(text=text, worth_question=False, reason="interrogative")

    if analyzed.root_verb and analyzed.root_verb.lower() in _IMPERATIVE_VERBS:
        return ScoredSentence(text=text, worth_question=False, reason="imperative")

    if words[0].lower().strip(":,.;") in _BOILERPLATE_OPENS:
        return ScoredSentence(text=text, worth_question=False, reason="boilerplate")

    if analyzed.root_verb is None:
        return ScoredSentence(text=text, worth_question=False, reason="no_verb")

    if analyzed.entities and analyzed.root_verb and analyzed.subject_text:
        return ScoredSentence(text=text, worth_question=True, reason="named_entity")

    if analyzed.root_verb and analyzed.subject_text and analyzed.nouns:
        return ScoredSentence(text=text, worth_question=True, reason="factual_claim")

    return ScoredSentence(text=text, worth_question=False, reason="no_claim")


def score_sentences(analyzed: list[AnalyzedSentence]) -> list[ScoredSentence]:
    return [score_sentence(sentence) for sentence in analyzed]