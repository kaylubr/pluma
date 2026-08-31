from core.services.analyze import analyze_sentence
from core.services.score import score_sentence, score_sentences
from core.tests.regression_sentences import REGRESSION_SENTENCES


class TestScoreSentence:
    def test_keep_named_entity_claim(self):
        analyzed = analyze_sentence("Marie Curie discovered polonium in 1898.")
        result = score_sentence(analyzed)
        assert result.worth_question is True
        assert result.reason == "named_entity"

    def test_keep_factual_claim_no_entity(self):
        analyzed = analyze_sentence("Cells are the basic unit of life.")
        result = score_sentence(analyzed)
        assert result.worth_question is True
        assert result.reason == "factual_claim"

    def test_keep_pptx_style_unpunctuated_bullet(self):
        analyzed = analyze_sentence("Mitochondria produce ATP")
        result = score_sentence(analyzed)
        assert result.worth_question is True

    def test_keep_passive_voice_claim(self):
        analyzed = analyze_sentence("ATP is produced by mitochondria")
        result = score_sentence(analyzed)
        assert result.worth_question is True

    def test_reject_interrogative(self):
        analyzed = analyze_sentence("Why do cells divide?")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "interrogative"

    def test_reject_unpunctuated_wh_question(self):
        analyzed = analyze_sentence("What is ATP")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "interrogative"

    def test_reject_imperative(self):
        analyzed = analyze_sentence("Define photosynthesis.")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "imperative"

    def test_reject_boilerplate(self):
        analyzed = analyze_sentence("Introduction to Cell Biology")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "boilerplate"

    def test_reject_fragment_no_verb(self):
        analyzed = analyze_sentence("The powerhouse of the cell")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "no_verb"

    def test_reject_named_entity_fragment(self):
        analyzed = analyze_sentence("Marie Curie")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "no_verb"

    def test_reject_single_word(self):
        analyzed = analyze_sentence("Yes")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "too_short"

    def test_reject_empty_input(self):
        result = score_sentence(analyze_sentence(""))
        assert result.worth_question is False
        assert result.reason == "empty"

    def test_reject_key_organelles_colon(self):
        analyzed = analyze_sentence("Key organelles:")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "no_verb"


class TestScoreSentences:
    def test_batch_matches_input_order(self):
        analyzed = [analyze_sentence(s) for s, _ in REGRESSION_SENTENCES]
        results = score_sentences(analyzed)
        assert len(results) == len(analyzed)
        for result, (_, expected) in zip(results, REGRESSION_SENTENCES):
            assert result.worth_question is expected

    def test_empty_list(self):
        assert score_sentences([]) == []