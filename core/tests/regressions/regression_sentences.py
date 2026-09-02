"""
Hand-labeled regression set for the Score stage.
Each entry is (sentence, expected_worth_question).
Run after any change to scoring logic — this extends the per-rule unit tests
with real lesson content to catch regressions that unit tests would miss.
"""
REGRESSION_SENTENCES = [
    # Reject: boilerplate / slide titles
    ("Introduction to Cell Biology", False),
    ("Key organelles:", False),
    ("ATP", False),
    ("The powerhouse of the cell", False),
    ("Why do cells divide?", False),

    # Reject: non-prose fragments from the smoke-test review
    ("Step 1: Tokenize the Text", False),
    ("s: +0.9 \u2192 2.5 + 0.9 = 3.4", False),

    # Reject: truncated list lead-in and example-value enumeration
    ("A common method is to:", False),
    ("Negative words: skinny (-1), bad (-1), hate (-1)", False),

    # Keep: factual claims from real lesson fixtures
    ("Cells are the basic unit of life", True),
    ("Mitochondria produce ATP", True),
    ("Ribosomes synthesize proteins", True),
    ("Nucleus contains DNA", True),
    ("DNA carries genetic information", True),
    ("Both organelles have their own DNA", True),
    ("ATP is produced by mitochondria", True),

    # Keep: named-entity factual claim
    ("Marie Curie discovered polonium in 1898.", True),
]