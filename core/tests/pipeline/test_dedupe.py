from core.services.dedupe import dedupe_questions
from core.tests.helper import make_cloze, make_validation


def _item(sentence_id, sentence, text, answer, is_valid=True, reasons=None):
    return (
        sentence_id,
        make_cloze(sentence, text, answer),
        make_validation(is_valid, reasons),
    )


class TestDedupeQuestions:
    def test_identical_card_marks_later_discarded(self):
        result = dedupe_questions(
            [
                _item(0, "A process waits on a mutex.", "A process waits on a _____.", "mutex"),
                _item(1, "A process waits on a mutex.", "A process waits on a _____.", "mutex"),
            ]
        )
        assert result[0][3] is False
        assert result[1][3] is True

    def test_answer_case_drift_still_duplicate(self):
        result = dedupe_questions(
            [
                _item(0, "A process waits on a mutex.", "A process waits on a _____.", "mutex"),
                _item(1, "A process waits on a mutex.", "A process waits on a _____.", "Mutex"),
            ]
        )
        assert result[0][3] is False
        assert result[1][3] is True

    def test_same_answer_in_different_questions_not_discarded(self):
        result = dedupe_questions(
            [
                _item(0, "Waiting on a mutex blocks the thread.", "Waiting on a _____ blocks the thread.", "mutex"),
                _item(1, "The mutex serializes access to the buffer.", "The _____ serializes access to the buffer.", "mutex"),
            ]
        )
        assert [item[3] for item in result] == [False, False]

    def test_three_near_duplicates_keep_first_only(self):
        item = lambda i: _item(
            i,
            "A process waits on a mutex that guards the buffer.",
            "A process waits on a _____ that guards the buffer.",
            "mutex",
        )
        result = dedupe_questions([item(0), item(1), item(2)])
        assert [item[3] for item in result] == [False, True, True]

    def test_slight_frame_drift_still_near_duplicate(self):
        result = dedupe_questions(
            [
                _item(0, "A process waits on a mutex that guards the buffer.", "A process waits on a _____ that guards the buffer.", "mutex"),
                _item(1, "A process waits on a mutex that guards the buffers.", "A process waits on a _____ that guards the buffers.", "mutex"),
            ]
        )
        assert result[0][3] is False
        assert result[1][3] is True

    def test_invalid_item_never_compared_and_untouched(self):
        result = dedupe_questions(
            [
                _item(0, "A process waits on a mutex.", "A process waits on a _____.", "mutex", is_valid=False, reasons=["too_short"]),
                _item(1, "A process waits on a mutex.", "A process waits on a _____.", "mutex"),
            ]
        )
        assert result[0][3] is False
        assert result[1][3] is False

    def test_preserves_count_order_and_only_changes_discarded(self):
        items = [
            _item(10, "Waiting on a mutex blocks the thread.", "Waiting on a _____ blocks the thread.", "mutex"),
            _item(20, "A process waits on a mutex.", "A process waits on a _____.", "mutex"),
            _item(30, "The mutex serializes access to the buffer.", "The _____ serializes access to the buffer.", "mutex"),
        ]
        result = dedupe_questions(items)
        assert len(result) == len(items)
        assert [item[0] for item in result] == [10, 20, 30]
        for (sentence_id, cloze, validation, discarded), (orig_id, orig_cloze, orig_valid) in zip(
            result, items
        ):
            assert sentence_id == orig_id
            assert cloze is orig_cloze
            assert validation is orig_valid
            assert isinstance(discarded, bool)

    def test_empty_input_returns_empty(self):
        assert dedupe_questions([]) == []
