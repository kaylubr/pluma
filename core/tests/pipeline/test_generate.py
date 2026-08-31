from core.services.generate import generate_cloze, generate_clozes
from core.tests.helper import make_analyzed
from core.tests.regressions.regression_clozes import REGRESSION_CLOZES


class TestGenerateClozeEntity:
    def test_blanks_first_entity_not_subject_aware(self):
        result = generate_cloze(
            make_analyzed(
                "Mitochondria produce ATP.",
                entities=[("Mitochondria", "PERSON")],
                nouns=["Mitochondria", "ATP"],
            )
        )
        assert result is not None
        assert result.sentence == "Mitochondria produce ATP."
        assert result.text == "_____ produce ATP."
        assert result.answer == "Mitochondria"
        assert result.reason == "entity"

    def test_blanks_whole_entity_over_component_nouns(self):
        result = generate_cloze(
            make_analyzed(
                "Marie Curie discovered polonium in 1898.",
                entities=[("Marie Curie", "PERSON"), ("1898", "DATE")],
                nouns=["Marie", "Curie", "polonium"],
            )
        )
        assert result is not None
        assert result.text == "_____ discovered polonium in 1898."
        assert result.answer == "Marie Curie"
        assert result.reason == "entity"

    def test_numeric_entity_never_becomes_candidate(self):
        result = generate_cloze(
            make_analyzed(
                "Cells were discovered in 1665.",
                entities=[("1665", "DATE")],
                nouns=["Cells"],
            )
        )
        assert result is not None
        assert result.text == "_____ were discovered in 1665."
        assert result.answer == "Cells"
        assert result.reason == "noun"


class TestGenerateClozeNoun:
    def test_blanks_first_noun_when_no_entity(self):
        result = generate_cloze(
            make_analyzed("Ribosomes synthesize proteins.", nouns=["proteins"])
        )
        assert result is not None
        assert result.text == "Ribosomes synthesize _____."
        assert result.answer == "proteins"
        assert result.reason == "noun"

    def test_blanks_first_noun_not_longest(self):
        result = generate_cloze(
            make_analyzed(
                "DNA carries genetic information.",
                nouns=["DNA", "information"],
            )
        )
        assert result is not None
        assert result.text == "_____ carries genetic information."
        assert result.answer == "DNA"
        assert result.reason == "noun"

    def test_blanks_subject_noun(self):
        result = generate_cloze(
            make_analyzed(
                "Cells are the basic unit of life.",
                nouns=["Cells", "unit", "life"],
            )
        )
        assert result is not None
        assert result.text == "_____ are the basic unit of life."
        assert result.answer == "Cells"
        assert result.reason == "noun"

    def test_blanks_passive_subject(self):
        result = generate_cloze(
            make_analyzed(
                "ATP is produced by mitochondria",
                nouns=["ATP", "mitochondria"],
            )
        )
        assert result is not None
        assert result.text == "_____ is produced by mitochondria"
        assert result.answer == "ATP"
        assert result.reason == "noun"

    def test_blanks_mid_sentence_noun(self):
        result = generate_cloze(
            make_analyzed(
                "Both organelles have their own DNA",
                nouns=["organelles", "DNA"],
            )
        )
        assert result is not None
        assert result.text == "Both _____ have their own DNA"
        assert result.answer == "organelles"
        assert result.reason == "noun"

    def test_skips_duplicate_candidate_and_falls_through(self):
        result = generate_cloze(
            make_analyzed(
                "ATP and DNA produce ATP.",
                nouns=["ATP", "DNA", "ATP"],
            )
        )
        assert result is not None
        assert result.text == "ATP and _____ produce ATP."
        assert result.answer == "DNA"
        assert result.reason == "noun"


class TestGenerateClozeNone:
    def test_all_candidates_duplicate_returns_none(self):
        result = generate_cloze(
            make_analyzed("DNA contains DNA.", nouns=["DNA", "DNA"])
        )
        assert result is None

    def test_no_candidates_returns_none(self):
        assert generate_cloze(make_analyzed("Yes")) is None

    def test_empty_text_returns_none(self):
        assert generate_cloze(make_analyzed("")) is None

    def test_whitespace_text_returns_none(self):
        assert generate_cloze(make_analyzed("   ")) is None


class TestGenerateClozeAnswerTraceability:
    def test_answer_is_word_boundary_match_in_sentence(self):
        for analyzed, _ in REGRESSION_CLOZES:
            result = generate_cloze(analyzed)
            if result is None:
                continue
            assert result.answer in analyzed.text


class TestGenerateClozes:
    def test_batch_matches_input_order_and_keeps_none(self):
        inputs = [
            make_analyzed("Ribosomes synthesize proteins.", nouns=["proteins"]),
            make_analyzed("Yes"),
            make_analyzed("Mitochondria produce ATP.", entities=[("Mitochondria", "PERSON")], nouns=["Mitochondria", "ATP"]),
        ]
        results = generate_clozes(inputs)
        assert len(results) == len(inputs)
        assert results[0].answer == "proteins"
        assert results[1] is None
        assert results[2].answer == "Mitochondria"

    def test_empty_list(self):
        assert generate_clozes([]) == []


class TestRegressionClozes:
    def test_regression_set_answers(self):
        for analyzed, expected_answer in REGRESSION_CLOZES:
            result = generate_cloze(analyzed)
            assert result is not None
            assert result.answer == expected_answer
