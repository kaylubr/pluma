from core.services.selection import select_document_questions
from core.tests.helper import make_cloze, make_validation


def _card(sentence, text, answer, is_valid=True, reasons=None):
    return (make_cloze(sentence, text, answer), make_validation(is_valid, reasons))


def _pool(sentence_id, *cards):
    return (sentence_id, list(cards))


class TestSelectDocumentQuestions:
    def test_declines_exact_duplicate_of_earlier_winner(self):
        result = select_document_questions(
            [
                _pool(0, _card("A process waits on a mutex.", "A process waits on a _____.", "mutex")),
                _pool(1, _card("A process waits on a mutex.", "A process waits on a _____.", "mutex")),
            ]
        )
        assert [item[0] for item in result] == [0]
        assert [item[1].answer for item in result] == ["mutex"]

    def test_declines_near_duplicate_with_plural_drift(self):
        result = select_document_questions(
            [
                _pool(
                    0,
                    _card(
                        "A process waits on a mutex that guards the buffer.",
                        "A process waits on a _____ that guards the buffer.",
                        "mutex",
                    ),
                ),
                _pool(
                    1,
                    _card(
                        "A process waits on a mutex that guards the buffers.",
                        "A process waits on a _____ that guards the buffers.",
                        "mutex",
                    ),
                ),
            ]
        )
        assert [item[0] for item in result] == [0]

    def test_same_answer_in_different_questions_kept_under_cap(self):
        result = select_document_questions(
            [
                _pool(0, _card("Waiting on a mutex blocks the thread.", "Waiting on a _____ blocks the thread.", "mutex")),
                _pool(1, _card("The mutex serializes access to the buffer.", "The _____ serializes access to the buffer.", "mutex")),
            ]
        )
        assert [item[0] for item in result] == [0, 1]

    def test_concept_cap_falls_back_to_next_candidate(self):
        result = select_document_questions(
            [
                _pool(0, _card("TextBlob returns a polarity score.", "_____ returns a polarity score.", "TextBlob")),
                _pool(1, _card("TextBlob splits sentences.", "_____ splits sentences.", "TextBlob")),
                _pool(
                    2,
                    _card("TextBlob can analyze text.", "_____ can analyze text.", "TextBlob"),
                    _card("TextBlob reports sentiment as a polarity value.", "TextBlob reports sentiment as a _____ value.", "polarity"),
                ),
            ]
        )
        assert [item[1].answer for item in result] == ["TextBlob", "TextBlob", "polarity"]

    def test_sentence_declined_when_only_candidate_over_cap(self):
        result = select_document_questions(
            [
                _pool(0, _card("TextBlob returns a polarity score.", "_____ returns a polarity score.", "TextBlob")),
                _pool(1, _card("TextBlob splits sentences.", "_____ splits sentences.", "TextBlob")),
                _pool(2, _card("TextBlob can analyze text.", "_____ can analyze text.", "TextBlob")),
            ]
        )
        assert [item[0] for item in result] == [0, 1]

    def test_invalid_only_sentence_keeps_best_invalid_marker(self):
        result = select_document_questions(
            [
                _pool(
                    0,
                    _card("Cells divide.", "_____ divide.", "Cells", is_valid=False, reasons=["too_short"]),
                ),
            ]
        )
        assert len(result) == 1
        assert result[0][0] == 0
        assert result[0][2].is_valid is False

    def test_no_fallback_to_invalid_when_valid_disqualified(self):
        result = select_document_questions(
            [
                _pool(0, _card("TextBlob returns a polarity score.", "_____ returns a polarity score.", "TextBlob")),
                _pool(1, _card("TextBlob splits sentences.", "_____ splits sentences.", "TextBlob")),
                _pool(
                    2,
                    _card("TextBlob can analyze text.", "_____ can analyze text.", "TextBlob"),
                    _card("Cells divide.", "_____ divide.", "Cells", is_valid=False, reasons=["too_short"]),
                ),
            ]
        )
        assert [item[0] for item in result] == [0, 1]

    def test_preserves_document_order_of_winners(self):
        result = select_document_questions(
            [
                _pool(10, _card("Waiting on a mutex blocks the thread.", "Waiting on a _____ blocks the thread.", "mutex")),
                _pool(20, _card("Ribosomes synthesize proteins.", "Ribosomes synthesize _____.", "proteins")),
                _pool(30, _card("Deadlock avoidance is studied here.", "_____ is studied here.", "Deadlock avoidance")),
            ]
        )
        assert [item[0] for item in result] == [10, 20, 30]
        for sentence_id, cloze, validation in result:
            assert isinstance(sentence_id, int)
            assert cloze.sentence
            assert isinstance(validation.is_valid, bool)

    def test_empty_input_returns_empty(self):
        assert select_document_questions([]) == []
