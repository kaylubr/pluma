from core.services.analyze import analyze_sentence
from core.services.score import score_sentence, score_sentences
from core.tests.regressions.regression_sentences import REGRESSION_SENTENCES


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
        assert result.reason == "lead_in"
        
    def test_reject_boilerplate_with_colon(self):
        analyzed = analyze_sentence("Overview: this unit covers cell structure.")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "boilerplate"


class TestScoreNonProseFragments:
    def test_reject_step_label(self):
        analyzed = analyze_sentence("Step 1: Tokenize the Text")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "step_label"

    def test_reject_phase_label_generalizes_beyond_step(self):
        analyzed = analyze_sentence("Phase 2: Normalize the corpus")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "step_label"

    def test_reject_unicode_arrow_notation(self):
        analyzed = analyze_sentence("s: +0.9 \u2192 2.5 + 0.9 = 3.4")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "notation"

    def test_reject_ascii_arrow_notation(self):
        analyzed = analyze_sentence("P1 -> P2 waiting")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "notation"

    def test_reject_symbol_heavy_expression(self):
        analyzed = analyze_sentence("2 + 2 = 4")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "symbol_heavy"

    def test_keep_sentence_containing_numbers(self):
        analyzed = analyze_sentence("Cells divide into two daughter cells during mitosis.")
        result = score_sentence(analyzed)
        assert result.worth_question is True

    def test_keep_boilerplate_colon_unaffected_by_new_rules(self):
        analyzed = analyze_sentence("Overview: this unit covers cell structure.")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "boilerplate"

    def test_keep_step_as_ordinary_vocabulary(self):
        analyzed = analyze_sentence("The next step in mitosis is anaphase.")
        result = score_sentence(analyzed)
        assert result.worth_question is True

    def test_reject_lead_in_ending_in_colon(self):
        analyzed = analyze_sentence("A common method is to:")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "lead_in"

    def test_reject_parenthesized_value_list(self):
        analyzed = analyze_sentence("Negative words: skinny (-1), bad (-1), hate (-1)")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "example_list"

    def test_keep_sentence_with_lone_parenthetical(self):
        analyzed = analyze_sentence("Ribosomes synthesize proteins in the cytoplasm.")
        result = score_sentence(analyzed)
        assert result.worth_question is True

    def test_keep_plain_propositional_sentence_with_digits(self):
        analyzed = analyze_sentence("The cell cycle has two main phases.")
        result = score_sentence(analyzed)
        assert result.worth_question is True

    def test_reject_mistagged_entity_fragment_without_subject(self):
        analyzed = analyze_sentence('Ignore neutral words like "girl" or "she."')
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "no_claim"

    def test_reject_entity_heading_without_subject(self):
        analyzed = analyze_sentence("Strategies for dealing with Deadlocks")
        result = score_sentence(analyzed)
        assert result.worth_question is False
        assert result.reason == "no_claim"

    def test_keep_entity_claim_with_real_subject(self):
        analyzed = analyze_sentence("Marie Curie discovered polonium in 1898.")
        result = score_sentence(analyzed)
        assert result.worth_question is True
        assert result.reason == "named_entity"


class TestScoreSentences:
    def test_batch_matches_input_order(self):
        analyzed = [analyze_sentence(s) for s, _ in REGRESSION_SENTENCES]
        results = score_sentences(analyzed)
        assert len(results) == len(analyzed)
        for result, (_, expected) in zip(results, REGRESSION_SENTENCES):
            assert result.worth_question is expected

    def test_empty_list(self):
        assert score_sentences([]) == []