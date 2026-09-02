"""
Hand-labeled regression set for the Generate stage.
Each entry is (AnalyzedSentence, expected_answer).
The AnalyzedSentence inputs are built by hand to mirror what the Analyze
stage produces for real lesson content, keeping this regression set free of
spaCy/NER coupling — real-parsing regressions are owned by test_analyze.py.
Run after any change to generation logic.
"""
from core.tests.helper import make_analyzed as _a


REGRESSION_CLOZES = [
    (
        _a("Mitochondria produce ATP.", entities=[("Mitochondria", "PERSON")], nouns=["Mitochondria", "ATP"]),
        "Mitochondria",
    ),
    (
        _a("Nucleus contains DNA.", entities=[("Nucleus", "PERSON")], nouns=["Nucleus", "DNA"]),
        "Nucleus",
    ),
    (
        _a("Ribosomes synthesize proteins.", nouns=["proteins"]),
        "proteins",
    ),
    (
        _a("DNA carries genetic information.", nouns=["DNA", "information"]),
        "DNA",
    ),
    (
        _a("Cells are the basic unit of life.", nouns=["Cells", "unit", "life"]),
        "Cells",
    ),
    (
        _a("ATP is produced by mitochondria", nouns=["ATP", "mitochondria"]),
        "mitochondria",
    ),
    (
        _a("Both organelles have their own DNA", nouns=["organelles", "DNA"]),
        "organelles",
    ),
    (
        _a(
            "Marie Curie discovered polonium in 1898.",
            entities=[("Marie Curie", "PERSON"), ("1898", "DATE")],
            nouns=["Marie", "Curie", "polonium"],
        ),
        "Marie Curie",
    ),
    (
        _a(
            "One-shot Algorithm - Given a request from process P for resources.",
            entities=[("Algorithm - Given", "ORG")],
            nouns=["Algorithm", "request", "process"],
        ),
        "Algorithm",
    ),
    (
        _a(
            "Lexicon-based methods analyze sentiment in product reviews.",
            nouns=["methods", "sentiment", "product", "reviews"],
            noun_phrases=["Lexicon-based methods"],
        ),
        "Lexicon-based methods",
    ),
    (
        _a("A process waits on a mutex.", nouns=["process", "mutex"]),
        "mutex",
    ),
    # Decline: the only blankable units are diagram identifiers, which are
    # reconstructable but test no knowledge.
    (
        _a(
            "Process A holds R and wants S",
            nouns=["Process", "A", "R", "S"],
            noun_phrases=["Process A"],
        ),
        None,
    ),
]
