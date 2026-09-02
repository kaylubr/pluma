from core.services.dedupe import dedupe_questions
from core.tests.helper import make_cloze, make_validation


def _item(sentence_id, answer, is_valid=True, reasons=None):
    sentence = f"Sentence {sentence_id} mentioning {answer}."
    text = f"Sentence {sentence_id} mentioning _____."
    return (
        sentence_id,
        make_cloze(sentence, text, answer),
        make_validation(is_valid, reasons),
    )


class TestDedupeQuestions:
    def test_exact_duplicate_marks_later_discarded(self):
        result = dedupe_questions([_item(0, "Resource"), _item(1, "Resource")])
        assert result[0][3] is False
        assert result[1][3] is True

    def test_case_insensitive_duplicate_marked_discarded(self):
        result = dedupe_questions([_item(0, "Resource"), _item(1, "resource")])
        assert result[0][3] is False
        assert result[1][3] is True

    def test_no_duplicates_nothing_discarded(self):
        result = dedupe_questions([_item(0, "Resource"), _item(1, "Process")])
        assert [item[3] for item in result] == [False, False]

    def test_three_duplicates_first_only_active(self):
        result = dedupe_questions(
            [_item(0, "Resource"), _item(1, "Resource"), _item(2, "Resource")]
        )
        assert [item[3] for item in result] == [False, True, True]

    def test_invalid_item_never_compared(self):
        result = dedupe_questions(
            [
                _item(0, "Resource", is_valid=False, reasons=["too_short"]),
                _item(1, "resource"),
            ]
        )
        assert result[0][3] is False
        assert result[1][3] is False

    def test_preserves_count_order_and_only_changes_discarded(self):
        items = [_item(10, "Resource"), _item(20, "resource"), _item(30, "Other")]
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
