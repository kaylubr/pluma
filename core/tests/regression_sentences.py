# Hand-labeled regression set for the Score stage.
# Each entry is (sentence, expected_worth_question).
# Run after any change to scoring logic — this extends the per-rule unit tests
# with real lesson content to catch regressions that unit tests would miss.
REGRESSION_SENTENCES = [
    # Reject: boilerplate / slide titles
    ("Introduction to Cell Biology", False),
    ("Key organelles:", False),
    ("ATP", False),
    ("The powerhouse of the cell", False),
    ("Why do cells divide?", False),

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