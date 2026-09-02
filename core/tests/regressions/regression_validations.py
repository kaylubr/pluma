"""
Hand-labeled regression set for the Validate stage.
Each entry is (AnalyzedSentence, GeneratedCloze, expected_is_valid).
Inputs are built by hand to mirror what Analyze/Generate produce for real
lesson content, keeping this regression set free of spaCy/NER coupling —
real-parsing regressions are owned by test_analyze.py.
Run after any change to validation logic.
"""
from core.tests.helper import make_analyzed as _a
from core.tests.helper import make_cloze as _c


REGRESSION_VALIDATIONS = [
    # Valid: real lesson sentences with a clean unique blank
    (
        _a("Cells are the basic unit of life."),
        _c("Cells are the basic unit of life.", "_____ are the basic unit of life.", "Cells"),
        True,
    ),
    (
        _a("Marie Curie Skłodowska discovered polonium."),
        _c("Marie Curie Skłodowska discovered polonium.", "_____ discovered polonium.", "Marie Curie Skłodowska"),
        True,
    ),
    # Invalid: fragment that slips past Score's 2-word floor but fails Validate's 5-word floor
    (
        _a("Cells divide."),
        _c("Cells divide.", "_____ divide.", "Cells"),
        False,
    ),
    # Invalid: bare pronoun subject
    (
        _a("It was discovered in 1898.", subject_is_pronoun=True),
        _c("It was discovered in 1898.", "_____ was discovered in 1898.", "It"),
        False,
    ),
    # Invalid: duplicated answer (ambiguous blank + answer leakage)
    (
        _a("DNA contains DNA."),
        _c("DNA contains DNA.", "_____ contains DNA.", "DNA"),
        False,
    ),
    # Valid: answer blanks a full candidate phrase span
    (
        _a(
            "The common method is to use a lexicon.",
            nouns=["method", "lexicon"],
            noun_phrases=["common method"],
        ),
        _c("The common method is to use a lexicon.", "The _____ is to use a lexicon.", "common method"),
        True,
    ),
    # Invalid: answer is a fragment of a candidate span, not the span itself
    (
        _a(
            "The common method is to use a lexicon.",
            nouns=["method", "lexicon"],
            noun_phrases=["common method"],
        ),
        _c("The common method is to use a lexicon.", "The _____ method is to use a lexicon.", "common"),
        False,
    ),
]
