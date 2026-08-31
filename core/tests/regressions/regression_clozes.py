"""
Hand-labeled regression set for the Generate stage.
Each entry is (AnalyzedSentence, expected_answer).
The AnalyzedSentence inputs are built by hand to mirror what the Analyze
stage produces for real lesson content, keeping this regression set free of
spaCy/NER coupling — real-parsing regressions are owned by test_analyze.py.
Run after any change to generation logic.
"""
from core.services.analyze import AnalyzedSentence


def _a(
    text: str,
    entities: list[tuple[str, str]] | None = None,
    nouns: list[str] | None = None,
) -> AnalyzedSentence:
    return AnalyzedSentence(
        text=text,
        entities=entities or [],
        nouns=nouns or [],
        root_verb=None,
        subject_text=None,
        subject_is_pronoun=False,
    )


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
        "ATP",
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
]
