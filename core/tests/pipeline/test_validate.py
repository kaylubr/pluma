from core.services.validate import validate_question, validate_questions
from core.tests.helper import make_analyzed, make_cloze
from core.tests.regressions.regression_validations import REGRESSION_VALIDATIONS


LONG_SENTENCE = (
    "Cellular respiration is the process by which cells convert the chemical "
    "energy stored in glucose into adenosine triphosphate and release carbon "
    "dioxide and water as waste products through a series of enzyme-catalyzed reactions."
)


class TestValidateQuestionPass:
    def test_valid_cloze_passes(self):
        sentence = "Cells are the basic unit of life."
        result = validate_question(
            make_analyzed(sentence),
            make_cloze(sentence, "_____ are the basic unit of life.", "Cells"),
        )
        assert result.is_valid is True
        assert result.reasons == []

    def test_multi_word_entity_answer_not_rejected_as_too_short(self):
        sentence = "Marie Curie Skłodowska discovered polonium."
        result = validate_question(
            make_analyzed(sentence),
            make_cloze(sentence, "_____ discovered polonium.", "Marie Curie Skłodowska"),
        )
        assert result.is_valid is True
        assert result.reasons == []


class TestValidateQuestionReject:
    def test_reject_too_short(self):
        sentence = "Cells divide."
        result = validate_question(
            make_analyzed(sentence),
            make_cloze(sentence, "_____ divide.", "Cells"),
        )
        assert result.is_valid is False
        assert "too_short" in result.reasons

    def test_reject_too_long(self):
        result = validate_question(
            make_analyzed(LONG_SENTENCE),
            make_cloze(LONG_SENTENCE, LONG_SENTENCE.replace("respiration", "_____"), "respiration"),
        )
        assert result.is_valid is False
        assert "too_long" in result.reasons

    def test_reject_bare_pronoun_subject(self):
        sentence = "It was discovered in 1898."
        result = validate_question(
            make_analyzed(sentence, subject_is_pronoun=True),
            make_cloze(sentence, "_____ was discovered in 1898.", "It"),
        )
        assert result.is_valid is False
        assert "bare_pronoun_subject" in result.reasons

    def test_reject_ambiguous_blank(self):
        sentence = "DNA contains DNA."
        result = validate_question(
            make_analyzed(sentence),
            make_cloze(sentence, "_____ contains DNA.", "DNA"),
        )
        assert result.is_valid is False
        assert "ambiguous_blank" in result.reasons

    def test_reject_answer_leakage(self):
        sentence = "DNA contains DNA."
        result = validate_question(
            make_analyzed(sentence),
            make_cloze(sentence, "_____ contains DNA.", "DNA"),
        )
        assert result.is_valid is False
        assert "answer_leakage" in result.reasons


class TestValidateQuestionRejectFragment:
    def test_reject_answer_that_is_not_a_full_candidate_span(self):
        sentence = "The common method is to use a lexicon."
        result = validate_question(
            make_analyzed(
                sentence,
                nouns=["method", "lexicon"],
                noun_phrases=["common method"],
            ),
            make_cloze(sentence, "The _____ method is to use a lexicon.", "common"),
        )
        assert result.is_valid is False
        assert "fragment_answer" in result.reasons

    def test_full_phrase_span_still_passes(self):
        sentence = "The common method is to use a lexicon."
        result = validate_question(
            make_analyzed(
                sentence,
                nouns=["method", "lexicon"],
                noun_phrases=["common method"],
            ),
            make_cloze(sentence, "The _____ is to use a lexicon.", "common method"),
        )
        assert result.is_valid is True
        assert result.reasons == []

    def test_fragment_check_skipped_when_no_candidates_known(self):
        sentence = "Cells are the basic unit of life."
        result = validate_question(
            make_analyzed(sentence),
            make_cloze(sentence, "_____ are the basic unit of life.", "Cells"),
        )
        assert result.is_valid is True
        assert result.reasons == []


class TestValidateQuestions:
    def test_batch_preserves_order_and_handles_none(self):
        analyzed_list = [
            make_analyzed("Cells are the basic unit of life."),
            make_analyzed("Cells divide."),
            make_analyzed("DNA contains DNA."),
        ]
        clozes = [
            make_cloze("Cells are the basic unit of life.", "_____ are the basic unit of life.", "Cells"),
            make_cloze("Cells divide.", "_____ divide.", "Cells"),
            None,
        ]
        results = validate_questions(analyzed_list, clozes)
        assert len(results) == len(analyzed_list)
        assert results[0].is_valid is True
        assert results[0].reasons == []
        assert results[1].is_valid is False
        assert "too_short" in results[1].reasons
        assert results[2].is_valid is False
        assert results[2].reasons == ["no_question"]

    def test_batch_raises_on_length_mismatch(self):
        try:
            validate_questions([make_analyzed("Cells divide.")], [])
        except ValueError:
            return
        assert False, "expected ValueError for mismatched list lengths"

    def test_empty_list(self):
        assert validate_questions([], []) == []


class TestRegressionValidations:
    def test_regression_set(self):
        for analyzed, cloze, expected_valid in REGRESSION_VALIDATIONS:
            result = validate_question(analyzed, cloze)
            assert result.is_valid is expected_valid
